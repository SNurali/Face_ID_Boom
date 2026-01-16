# app/utils/validation.py
from pydantic import BaseModel, validator, ValidationError as PydanticValidationError
from typing import Optional
from datetime import date

class ValidationError(Exception):
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)

def validate_passport_number(passport: str) -> None:
    if not passport or not passport.strip():
        raise ValidationError("Номер паспорта обязателен", "passport")

def validate_full_name(full_name: str) -> None:
    if not full_name or not full_name.strip():
        raise ValidationError("ФИО обязательно", "full_name")

def validate_sex(sex: int) -> None:
    if sex not in [1, 2]:
        raise ValidationError("Пол должен быть 1 (муж) или 2 (жен)", "sex")

def validate_date_of_birth(dob: Optional[str]) -> None:
    if dob:
        try:
            date.fromisoformat(dob)
        except ValueError:
            raise ValidationError("Неверный формат даты рождения (ожидается YYYY-MM-DD)", "date_of_birth")

def validate_visa_fields(visa_type: Optional[str], visa_number: Optional[str],
                        visa_organ: Optional[str], visa_date_from: Optional[str],
                        visa_date_to: Optional[str]) -> None:
    fields = [visa_type, visa_number, visa_organ, visa_date_from, visa_date_to]
    non_null = sum(1 for f in fields if f is not None and (isinstance(f, str) and f.strip()))
    if 0 < non_null < 5:
        raise ValidationError("Все поля визы должны быть указаны вместе или не указаны вовсе", "visa")

def validate_all_register_fields(input_data: BaseModel) -> None:
    # Здесь вызываем все проверки
    validate_passport_number(getattr(input_data, 'passport', ''))
    validate_full_name(getattr(input_data, 'full_name', ''))
    validate_sex(getattr(input_data, 'sex', 0))
    validate_date_of_birth(getattr(input_data, 'date_of_birth', None))
    validate_visa_fields(
        getattr(input_data, 'visa_type', None),
        getattr(input_data, 'visa_number', None),
        getattr(input_data, 'visa_organ', None),
        getattr(input_data, 'visa_date_from', None),
        getattr(input_data, 'visa_date_to', None)
    )