"""

Layers starting from lowest:

    0. BoundAttr.value
    1. Attr.__get__,  Attr.__set__
    2. Attrs.get, Attrs.set

"""
import collections
import inspect
from copy import copy

ATTRS_FOR_CONTAINER_CLS = '_attrs_for_cls_'
ATTRS_FOR_CONTAINER_INSTANCE = '_attrs_'
ATTRS_ALL_NAMES = '_attrs_all_names_'


def invoke_with_extras(func, **extras):
    """
    Invoke the function with extras populating any corresponding args or kwargs.
    """
    signature = inspect.signature(func)  # type: inspect.Signature

    bound_args = signature.bind(
        **{k: extras.pop(k) for k in list(extras.keys()) if k in signature.parameters}
    )  # type: inspect.BoundArguments
    return func(*bound_args.args, **bound_args.kwargs)


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
    _internals_ = (
        'name', 'required', 'default', '_f_get_value', '_f_set_value', '_f_init_value', 'options',
    )

    def __init__(
            self, *args,
            name=None, default=NotSet, required=False,
            get_value=None, set_value=None, init_value=None,
            **options
    ):
        if args:
            assert len(args) == 1
            if isinstance(args[0], str):
                assert name is None
                name = args[0]
            elif callable(args[0]):
                # This allows using "@Attr" as a decorator for Attr.get_value method,
                # just like "@property" by default is for getter.
                assert get_value is None
                get_value = args[0]
            else:
                raise TypeError('Unrecognised args: {}'.format(args))

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

    def __call__(self, get_value_method):
        self._f_get_value = get_value_method
        return self

    def init_value(*args):
        return process_fattr_decorator('init_value', args)

    def get_value(*args):
        return process_fattr_decorator('get_value', args)

    def set_value(*args):
        return process_fattr_decorator('set_value', args)

    def __getattr__(self, name):
        if name == 'options':  # avoid recursion due to copying
            raise AttributeError('options')
        if name in self.options:
            return self.options[name]
        raise AttributeError(name)

    def __setattr__(self, name, value):
        if name in self._internals_:
            super().__setattr__(name, value)
        elif name in self.options:
            self.options[name] = value
        else:
            raise AttributeError(name)


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
        elif hasattr(self.attr, name):
            if not isinstance(self.owner, type):
                raise TypeError('Cannot set attribute {!r} on instance-bound Attr {!r}'.format(name, self.attr.name))
            setattr(self.attr, name, value)
        else:
            # Do not allow setting Attr attributes through here
            raise AttributeError(name)

    @property
    def value(self):
        # Do not override this logic. Add features in Attrs.get
        if isinstance(self.owner, type):
            raise TypeError('Attr has value only when bound to a container instance, not container class')
        else:
            if not self.has_value_initialised:
                self.init_value()
            return getattr(self.owner, self.storage_name)

    @value.setter
    def value(self, new):
        # Do not override this logic. Add features in Attrs.set
        if isinstance(self.owner, type):
            raise TypeError('{} on class is read-only'.format(self.attr.name))
        if not self.has_value_initialised:
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
        """
        Only to be called to set the value the first time
        """

        # Set a temporary value so that initialiser can safely
        # call value setter and avoid infinite recursion
        setattr(self.owner, self.storage_name, TempValue)

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

    @property
    def _names_(self):
        if isinstance(self.owner, type):
            return getattr(self.owner, ATTRS_ALL_NAMES)
        else:
            return getattr(self.owner.__class__, ATTRS_ALL_NAMES)

    @property
    def _all_(self):
        return (getattr(self, name) for name in self._names_)

    def _tagged_(self, *tags):
        for attr in self._all_:
            if all(getattr(attr, tag, None) for tag in tags):
                yield attr

    def _process_(self, payload: dict, apply=True, consume=False, ignore_unknown=False):
        for k, v in list(payload.items()):
            if k in self:
                if apply:
                    self.set(k, v)
                if consume:
                    payload.pop(k)
            else:
                if not ignore_unknown:
                    raise AttributeError(k)

    def _update_(self, *args, **kwargs):
        if args:
            assert len(args) == 1
            assert isinstance(args[0], dict)
            return self._process_(args[0])
        else:
            return self._process_(kwargs)

    def __contains__(self, name):
        if isinstance(self.owner, type):
            return isinstance(getattr(self.owner, name, None), Attr)
        else:
            return isinstance(getattr(self.owner.__class__, name, None), Attr)

    def __getitem__(self, name):
        if name not in self.bound_attrs:

            # We are looking for attribute that is a descriptor of class Attr.
            # This means we must NOT check instance attribute value, but instead
            # check class attribute which will be the descriptor itself.
            if isinstance(self.owner, type):
                attr = getattr(self.owner, name)
            else:
                attr = getattr(self.owner.__class__, name)

            # If it's not ours then it shouldn't be accessed via attrs.
            if not isinstance(attr, Attr):
                if isinstance(self.owner, type):
                    raise AttributeError('{}.{} is not an Attr'.format(self.owner.__name__, name))
                else:
                    raise AttributeError('{}.{} is not an Attr'.format(self.owner.__class__.__name__, name))

            self.bound_attrs[name] = self.owner.bound_attr_cls(self.owner, attr)

        return self.bound_attrs[name]

    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        if name in self._internals_:
            super().__setattr__(name, value)
        else:
            raise AttributeError('Attribute {!r} is read-only'.format(name))

    def __iter__(self):
        yield from self._names_


class ContainerMeta(type):
    def __new__(meta, name, bases, dct):
        base_attrs = collections.OrderedDict()

        attrs_all_names = []

        for base in bases[0].__mro__ if bases else ():
            for k, v in base.__dict__.items():
                if isinstance(v, Attr):
                    base_attrs[k] = v
                    if v.name is None:
                        v.name = k
                    if v.name not in attrs_all_names:
                        attrs_all_names.append(v.name)

        for k, v in list(dct.items()):
            if isinstance(v, Attr):
                if v.name is None:
                    v.name = k
                if v.name not in attrs_all_names:
                    attrs_all_names.append(v.name)
            elif k in base_attrs:
                dct[k] = copy(base_attrs[k])
                dct[k].default = v

        dct[ATTRS_ALL_NAMES] = attrs_all_names

        container_cls = super().__new__(meta, name, bases, dct)

        return container_cls


class _AttrsProperty:
    def __get__(self, instance, owner):
        if instance is None:
            # Must check against __dict__ because the attribute may have been set
            # against parent class and we would fail to initialise the class-specific
            # attribute list.
            if ATTRS_FOR_CONTAINER_CLS not in owner.__dict__:
                setattr(owner, ATTRS_FOR_CONTAINER_CLS, owner.attrs_cls(owner))
            return getattr(owner, ATTRS_FOR_CONTAINER_CLS)
        else:
            if not hasattr(instance, ATTRS_FOR_CONTAINER_INSTANCE):
                setattr(instance, ATTRS_FOR_CONTAINER_INSTANCE, instance.attrs_cls(instance))
            return getattr(instance, ATTRS_FOR_CONTAINER_INSTANCE)

    def __set__(self, instance, value):
        raise AttributeError('{}.attrs is read-only'.format(instance.__class__.__name__))


class ContainerBase(metaclass=ContainerMeta):
    attrs_cls = Attrs
    bound_attr_cls = BoundAttr

    attrs = _AttrsProperty()

    def __init__(self, *args, **kwargs):
        for k in list(kwargs.keys()):
            if k in self.attrs:
                self.attrs[k].value = kwargs.pop(k)
        super().__init__(*args, **kwargs)


def container(container_cls):
    return type(container_cls.__name__, (container_cls, ContainerBase), {})
