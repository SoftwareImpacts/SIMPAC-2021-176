class Infix:
    def __init__(self, func, value = None):
        self.func = func
        self.value = value
    
    def __lshift__(self,other):
        print(1)
        
    def __rlshift__(self, other):
        print(2)
        return Infix(self.func, other)
    
    def __rshift__(self, other):
        print(3)
        
    def __rrshift__(self, other):
        print(4)
    
iadd = Infix(lambda x:x)

__all__ = ['iadd']