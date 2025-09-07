import datetime
from dataclasses import dataclass
from typing import Any

from mywallet.wallet.model import Asset, Place, Price, TransactionType


@dataclass
class TransactionState:
    total_questions: int = 5
    place: Place | None = None
    price: Price | None = None
    type: TransactionType | None = None
    date: datetime.date | None = None
    asset: Asset | None = None
    current_question: int = 0

    def _next_question(self):
        if self.current_question < self.total_questions:
            self.current_question += 1
        else:
            # TODO : Enregristrer la transaction
            pass

    def previous_question(self):
        if self.current_question > 0:
            self.current_question -= 1

    def reset(self):
        self.place = None
        self.current_question = 0
        self.price = None
        self.type = None
        self.date = None
        self.asset = None

    def register(self, answer: Any) -> int:
        match self.current_question:
            case 0:
                self.type = answer
            case 1:
                self.asset = answer
            case 2:
                self.date = answer
            case 3:
                self.price = answer
            case 4:
                self.place = answer
            case _:
                raise ValueError("Invalid question index")
        self._next_question()
        return self.current_question
