def test_verification_service_is_importable():
    from app.verification import VerificationService, VerificationRecord
    assert VerificationService is not None
    assert VerificationRecord is not None
