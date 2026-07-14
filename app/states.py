from aiogram.fsm.state import State, StatesGroup


class RegistrationState(StatesGroup):
    waiting_for_name = State()
    waiting_for_contact = State()


class CheckState(StatesGroup):
    waiting_for_plate = State()
