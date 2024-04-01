class Base:
    top_class_name = None

    def __init__(self):
        self.top_class_name = self.__class__.__name__        
        print("Subclass top class name:", self.top_class_name)

        

# Example usage
class Subclass(Base):
    def __init__(self):
        super().__init__()  # Call the __init__ method of the base class
        print("Subclass top class name:", self.top_class_name)

# Example usage
class Subclass2(Base):
    def __init__(self):
        super().__init__()  # Call the __init__ method of the base class
        print("Subclass top class name:", self.top_class_name)


# Create an instance of SubSubclass
sub_sub_instance = Subclass()
sub_sub_instance = Subclass2()
