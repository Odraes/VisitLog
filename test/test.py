# ---------- OOP examples (encapsulation, inheritance, polymorphism, abstract) ----------
# Encapsulation: BankAccount with private balance and controlled accessors
class BankAccount:
    def __init__(self, owner: str, balance: float = 0.0):
        self.owner = owner
        self.__balance = float(balance)

    @property
    def balance(self) -> float:
        """Read-only access to the private balance."""
        return self.__balance

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self.__balance += amount

    def withdraw(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Withdraw amount must be positive")
        if amount > self.__balance:
            raise ValueError("Insufficient funds")
        self.__balance -= amount

    def __repr__(self) -> str:
        return f"BankAccount(owner={self.owner!r}, balance={self.__balance})"


# Inheritance + Method Overriding: Animal base class, Dog and Cat override speak()
class Animal:
    def speak(self) -> str:
        return "..."


class Dog(Animal):
    def speak(self) -> str:
        return "Woof"


class Cat(Animal):
    def speak(self) -> str:
        return "Meow"


# Polymorphism demo helper: call speak() on any Animal-like object
def animal_sounds(animals):
    return [a.speak() for a in animals]


# Abstract class (Interface) example using abc.ABC
class Vehicle(abc.ABC):
    @abc.abstractmethod
    def drive(self) -> str:
        pass


class Car(Vehicle):
    def drive(self) -> str:
        return "Car is driving"


class Bike(Vehicle):
    def drive(self) -> str:
        return "Bike is driving"


# Demo route that exercises the examples and returns JSON-friendly data
@app.route('/oop-demo')
def oop_demo():
    acc = BankAccount("Alice", 100)
    acc.deposit(50)
    try:
        acc.withdraw(30)
    except Exception:
        pass

    animals = [Dog(), Cat()]
    sounds = animal_sounds(animals)

    vehicles = [Car(), Bike()]
    drives = [v.drive() for v in vehicles]

    return {
        "encapsulation": {"owner": acc.owner, "balance": acc.balance},
        "polymorphism": sounds,
        "vehicles": drives,
    }

