import datetime

from mywallet.wallet.model import (
    Asset,
    AssetId,
    AssetType,
    Currency,
    Place,
    PlaceId,
    Price,
    PriceId,
    TransactionType,
)
from src.mywallet.ui.features.transaction.transaction_state import TransactionState


def test_transaction_state_register(mocker):
    module = TransactionState.__module__
    mock_add_transaction = mocker.patch(f"{module}.add_transaction")
    mocker.patch(f"{module}.st")
    state = TransactionState()
    assert state.current_question == 0

    # Register type
    type = TransactionType("buy")
    next_question = state.register(type)
    assert next_question == 1
    assert state.type == type

    # Register asset
    asset = Asset(
        id=AssetId("1"),
        name="Bitcoin",
        ticker="BTC",
        type=AssetType("crypto"),
        category=[],
    )
    next_question = state.register(asset)
    assert next_question == 2
    assert state.asset == asset

    # Register date
    date = datetime.date(year=2024, month=1, day=1)
    next_question = state.register(date)
    assert next_question == 3
    assert state.date == date

    # Register price
    price = Price(id=PriceId("1"), amount=50000.0, currency=Currency("€"))
    next_question = state.register(price)
    assert next_question == 4
    assert state.price == price

    # Register place
    place = Place(id=PlaceId("1"), name="Coinbase", description="Crypto Exchange")
    next_question = state.register(place)

    # At this point, the transaction should be complete and reset
    assert state.current_question == 0
    assert state.type is None
    assert state.asset is None
    assert state.date is None
    assert state.price is None
    assert state.place is None
    assert mock_add_transaction.call_count == 1


def test_transaction_state_register_invalid_question(mocker):
    mocker.patch("mywallet.ui.features.transaction.transaction_state.st")
    state = TransactionState()
    # Register type
    type = TransactionType("buy")
    next_question = state.register(type)
    assert next_question == 1
    assert state.type == type

    # Register asset
    price = Price(id=PriceId("1"), amount=50000.0, currency=Currency("€"))
    try:
        state.register(price)  # Invalid at this step
    except Exception as e:
        assert isinstance(e, AssertionError)
