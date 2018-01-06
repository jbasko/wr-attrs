# wr-attrs


 * Attributes are descriptors for classes and values for instances 
 
        class A(AttrContainer):
            p = Attr()
        
        a = A()
        
        assert isinstance(A.p, Attr)
        assert A.p.name == 'p' 
        assert A.p.default is None
        
        assert a.p is None
 
 * Attributes can be easily initialised
 
        a = A(p=23)
        
        assert isinstance(A.p, Attr)
        assert A.p.default is None
        
        assert a.p == 23
        
 * Attributes are inherited
 
        class B(A):
            q = Attr()
            r = Attr()
        
        b = B(p=23, q=42)

        assert B.p is A.p
        
        assert b.p == 23
        assert b.q == 42
        assert b.r is None


 * Attributes are registered in a collection.
 
        b = B(q=42)

        assert len(b.attrs) == 3
        assert b.attrs.names == ['p', 'q', 'r']
        assert list(b.attrs.values) == [('p', None), ('q', 42), ('r', None)]
        
        assert b.attrs.q is B.q
        assert b.attrs['q'] is B.q
        assert b.attrs.get('q') == 42
 

 * Attributes can have default values set in inherited classes without overwriting
   the descriptor.
   
        class C(B):
            p = 0
            q = 1
   
        c = C()

        assert c.p == 0
        assert c.q == 1
        assert c.r is None
    
        assert C.p is B.p
        assert C.q is B.q
        assert C.r is B.r
 
 * Attributes can have custom setters.
 
        class D(C):
            s = Attr()
            
            @s.setter
            def s(self, value):
                self.attrs.set('s', value * 5)

        d = D(s=0)
        d.s = 5
        assert d.s == 25
