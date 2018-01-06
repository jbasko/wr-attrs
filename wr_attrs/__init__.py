__version__ = '0.1.1'


import collections
import copy


class Attr:
    """
    Descriptor to declare rich attributes in classes that inherit AttrContainer.

    Deletion of Attr attribute is not permitted because of unclear semantics.
    """

    ALL_ATTRS = '_all_attrs_'

    def __init__(self, name=None, default=None, fget=None, fset=None, doc=None, **options):
        self.name = name

        self.default = default

        self.options = options

        self._storage_name = None

        self.fget = fget
        self.fset = fset
        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc

    @property
    def storage_name(self):
        if self._storage_name is None:
            assert self.name
            self._storage_name = '_{}#{}'.format(self.__class__.__name__, self.name)
        return self._storage_name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if self.fget is None:
            return instance.attrs.get(self.name, self.default)
        return self.fget(instance)

    def __set__(self, instance, value):
        if self.fset is None:
            instance.attrs.set(self.name, value)
            return
        self.fset(instance, value)

    def __repr__(self):
        return '<{} {!r}>'.format(self.__class__.__name__, self.name)

    def getter(self, fget):
        """
        Decorator to register a getter of Attr.
        The method must have the same name as the Attr.

        In getter, to access the low-level storage, use self.attrs.get(name, default).
        """
        self.fget = fget
        assert self.name is None or fget.__name__ == self.name

        # Must return self so that in class dictionary the getter function doesn't overwrite
        # the descriptor itself.
        return self

    def setter(self, fset):
        """
        Decorator to register a setter of Attr.
        The method must have the same name as the Attr.

        In setter, to access the low-level storage, use self.attrs.set(name, value).
        """
        self.fset = fset
        assert self.name is None or fset.__name__ == self.name

        # Must return self so that in class dictionary the setter function doesn't overwrite
        # the descriptor itself.
        return self

    def __copy__(self):
        return self.__class__(
            name=self.name,
            default=self.default,
            options=dict(self.options),
            fset=self.fset,
            fget=self.fget,
            doc=self.__doc__,
        )


class _Attrs:
    """
    A wrapper that simplifies access to the attrs set on container class or instance.
    """

    def __init__(self, owner):
        self.owner = owner

    def set(self, name, value):
        """
        This is the ultimate lowest level method of setting actual attribute value
        in instance dictionary.
        """
        if name not in self.names:
            raise AttributeError(name)
        if isinstance(self.owner, type):
            setattr(self.owner, name, value)
        else:
            setattr(self.owner, self[name].storage_name, value)

    def get(self, name, default=None):
        """
        This is the ultimate lowest level method for getting actual attribute
        value from instance dictionary.
        """
        if isinstance(self.owner, type):
            return getattr(self.owner, name)
        else:
            return getattr(self.owner, self[name].storage_name, default)

    def update(self, *args, **kwargs):
        if args:
            assert len(args) == 1
            assert not kwargs
            kwargs = args[0]
        for key in self.names:
            if key in kwargs:
                self.set(key, kwargs.pop(key))
        if kwargs:
            raise AttributeError(list(kwargs.keys())[0])

    @property
    def values(self):
        return ((k, self.get(k)) for k in self.names)

    @property
    def names(self):
        """
        Returns names of all attributes.
        """
        return self.collection.keys()

    @property
    def collection(self):
        return getattr(self.owner, Attr.ALL_ATTRS)

    def __repr__(self):
        return '<{} of {}>'.format(self.__class__.__name__, self.owner)

    def __getattr__(self, name):
        try:
            return self.collection[name]
        except KeyError:
            raise AttributeError(name)

    def __getitem__(self, name):
        return self.collection[name]

    def __contains__(self, name):
        return name in self.collection

    def __len__(self):
        return len(self.collection)

    def __bool__(self):
        return bool(self.collection)


class _AttrContainerMeta(type):
    """
    Meta class for AttrContainer.
    """

    def __new__(meta, name, bases, dct):
        all_attrs = collections.OrderedDict()

        # Populate all_attrs collection with all inherited attributes

        attrs_cls = None

        for base in bases:
            if hasattr(base, 'attrs_cls'):
                attrs_cls = getattr(base, 'attrs_cls')

            if not hasattr(base, Attr.ALL_ATTRS):
                continue

            for attr_name in getattr(base, Attr.ALL_ATTRS):
                attr = getattr(base, attr_name)
                assert isinstance(attr, Attr)
                assert attr.name == attr_name

                if attr_name not in all_attrs:
                    all_attrs[attr_name] = attr

        # Process new class dictionary

        for k in list(dct.keys()):
            if isinstance(dct[k], Attr):
                # Declaration of an attribute.
                # Must set Attr.name if necessary.
                attr = dct[k]
                assert attr.name is None or attr.name == k
                attr.name = k

                # Register Attr in all_attrs collection.
                all_attrs[k] = attr

            elif k in all_attrs:
                # User is setting a class-specific default value for an existing attribute
                new_default = dct[k]
                dct[k] = copy.copy(all_attrs[k])
                dct[k].default = new_default
                all_attrs[k] = dct[k]

        if dct.get('attrs_cls'):
            attrs_cls = dct['attrs_cls']

        dct[Attr.ALL_ATTRS] = all_attrs

        container_cls = super().__new__(meta, name, bases, dct)

        # AttrContainer class also has attrs which are not bounded to any instance.
        container_cls.attrs = attrs_cls(container_cls)  # type: _Attrs

        return container_cls


class AttrContainer(metaclass=_AttrContainerMeta):
    """
    Attribute container -- base class for user classes that want to use Attr(s).
    """

    attrs_cls = _Attrs

    def __init__(self, **kwargs):
        self.attrs_cls = kwargs.pop('attrs_cls', self.attrs_cls)
        self.attrs = self.attrs_cls(self)  # type: _Attrs
        self.attrs.update(**kwargs)

    def __repr__(self):
        return '<{} at {}>'.format(self.__class__.__name__, id(self))
