"""

Layers starting from lowest:

    0. BoundAttr.value
    1. Attr.__get__,  Attr.__set__
    2. Attrs.get, Attrs.set

"""
import collections
import inspect
from copy import copy


def invoke_with_extras(func, **extras):
    """
    Invoke the function with extras populating any corresponding args or kwargs.
    """
    signature = inspect.signature(func)  # type: inspect.Signature

    bound_args = signature.bind(
        **{k: v for k, v in extras.items() if k in signature.parameters}
    )  # type: inspect.BoundArguments
    return func(*bound_args.args, *bound_args.kwargs)


def process_fattr_decorator(decorator_name, args):
    fattr_name = '_f_{}'.format(decorator_name)
    if len(args) == 1:
        func = args[0]
        attr = Attr(name=func.__name__, **{decorator_name: func})
        return attr
    else:
        assert len(args) == 2
        attr, func = args
        assert func.__name__ == attr.name or attr.name is None
        attr.name = func.__name__
        setattr(attr, fattr_name, func)
        return attr


class _Falsey:
    def __init__(self, name):
        self._name = name

    def __bool__(self):
        return False

    def __repr__(self):
        return '<{}>'.format(self._name)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self._name == other._name


NotSet = _Falsey('NotSet')
Required = _Falsey('Required')
TempValue = _Falsey('TempValue')


class Attr:
    def __init__(self, name=None, default=NotSet, required=False, get_value=None, set_value=None, init_value=None, **options):
        self.name = name  # type: str

        self.required = bool(required)
        if default is NotSet:
            if self.required:
                self.default = Required
            else:
                self.default = None
        else:
            if self.required:
                raise ValueError('default= must not be set together with required=True')
            self.default = default

        self._f_get_value = get_value  # type: callable
        self._f_set_value = set_value  # type: callable
        self._f_init_value = init_value  # type: callable

        self.options = options

    def __set__(self, instance, value):
        # Do not override this logic. Add features in Attrs.value
        if self._f_set_value is None:
            instance.attrs.set(self.name, value)
        else:
            invoke_with_extras(self._f_set_value, self=instance, attr=instance.attrs[self.name], value=value)

    def __get__(self, instance, owner: type):
        # Do not override this logic. Add features in Attrs.get
        if instance is None:
            return self
        else:
            if self._f_get_value is None:
                return instance.attrs.get(self.name)
            else:
                return invoke_with_extras(self._f_get_value, self=instance, attr=instance.attrs[self.name])

    def __delete__(self, instance):
        raise NotImplementedError()

    def __repr__(self):
        return '<{} {!r}>'.format(self.__class__.__name__, self.name)

    def init_value(*args):
        return process_fattr_decorator('init_value', args)

    def get_value(*args):
        return process_fattr_decorator('get_value', args)

    def set_value(*args):
        return process_fattr_decorator('set_value', args)


class BoundAttr:
    # Internals are attributes which are not delegated to (owner, attr)
    _internals_ = ('owner', 'attr', 'value', 'storage_name')

    def __init__(self, owner, attr: Attr):
        self.owner = owner
        self.attr = attr

        # The name under which the attribute value is stored in owner's __dict__
        assert self.owner
        assert self.attr.name
        self.storage_name = '{}#{}'.format(self.owner.__class__.__name__, self.attr.name)

    def __repr__(self):
        return '<{} {}.{}>'.format(self.__class__.__name__, self.owner.__class__.__name__, self.attr.name)

    def __getattr__(self, name):
        return getattr(self.attr, name)

    def __setattr__(self, name, value):
        if name in self._internals_:
            super().__setattr__(name, value)
        else:
            # Do not allow setting Attr attributes through here
            raise AttributeError(name)

    @property
    def value(self):
        # Do not override this logic. Add features in Attrs.get
        if isinstance(self.owner, type):
            return getattr(self.owner, self.attr.name)
        else:
            if not self.has_value_initialised:
                self.init_value()
            return getattr(self.owner, self.storage_name)

    @value.setter
    def value(self, new):
        # Do not override this logic. Add features in Attrs.set
        if isinstance(self.owner, type):
            raise AttributeError('{} on class is read-only'.format(self.attr.name))
        if not self.has_value_initialised:
            # Set a temporary value so that initialiser can safely
            # call value setter and avoid infinite recursion
            setattr(self.owner, self.storage_name, TempValue)
            self.init_value(value=new)

            # set_value should see the initialised value.
            new = self.value

        setattr(self.owner, self.storage_name, new)

    @property
    def has_value_initialised(self):
        """
        Returns True if instance has anything stored under the storage_name of this attribute.
        """
        return hasattr(self.owner, self.storage_name)

    def init_value(self, value=NotSet):
        # Only to be called to set the value the first time
        if value is NotSet:
            value = self.default
        if self._f_init_value:
            invoke_with_extras(self._f_init_value, self=self.owner, attr=self, value=value)
        else:
            setattr(self.owner, self.storage_name, value)


class Attrs:
    _internals_ = ('owner', 'bound_attrs')

    def __init__(self, owner):
        self.owner = owner
        self.bound_attrs = {}

    def get(self, attr_name: str):
        attr = self[attr_name]

        if attr.required and attr.value is Required:
            raise ValueError('Required attr {!r} is missing value'.format(attr_name))

        return attr.value

    def set(self, attr_name: str, new):
        attr = self[attr_name]
        attr.value = new

    def __contains__(self, name):
        return isinstance(getattr(self.owner.__class__, name, None), Attr)

    def __getitem__(self, name):
        if name not in self.bound_attrs:
            attr = getattr(self.owner.__class__, name)
            if not isinstance(attr, Attr):
                raise AttributeError('{}.{} is not an Attr'.format(self.owner.__class__.__name__, name))
            self.bound_attrs[name] = self.owner.bound_attr_cls(self.owner, attr)
        return self.bound_attrs[name]

    def __setitem__(self, name, value):
        raise KeyError('Key {!r} is read-only'.format(name))

    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        if name in self._internals_:
            super().__setattr__(name, value)
        else:
            raise AttributeError('Attribute {!r} is read-only'.format(name))


class ContainerMeta(type):
    def __new__(meta, name, bases, dct):
        base_attrs = collections.OrderedDict()

        for base in bases[0].__mro__ if bases else ():
            for k, v in base.__dict__.items():
                if isinstance(v, Attr):
                    base_attrs[k] = v
                    if v.name is None:
                        v.name = k

        for k, v in list(dct.items()):
            if isinstance(v, Attr):
                if v.name is None:
                    v.name = k
            elif k in base_attrs:
                dct[k] = copy(base_attrs[k])
                dct[k].default = v

        return super().__new__(meta, name, bases, dct)


class ContainerBase(metaclass=ContainerMeta):
    attrs_cls = Attrs
    bound_attr_cls = BoundAttr

    def __init__(self, *args, **kwargs):
        for k in list(kwargs.keys()):
            if k in self.attrs:
                self.attrs[k].value = kwargs.pop(k)
        super().__init__(*args, **kwargs)

    @property
    def attrs(self):
        if not hasattr(self, '_attrs_'):
            setattr(self, '_attrs_', self.attrs_cls(self))
        return getattr(self, '_attrs_')


def container(container_cls):
    return type(container_cls.__name__, (container_cls, ContainerBase), {})
