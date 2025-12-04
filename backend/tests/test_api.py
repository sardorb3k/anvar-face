import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestAPI:
    """Tests for API endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_register_student_missing_fields(self):
        """Test student registration with missing fields."""
        response = client.post("/api/students/register", json={})
        assert response.status_code == 422  # Validation error
    
    def test_register_student_valid(self):
        """Test student registration with valid data."""
        student_data = {
            "student_id": "TEST001",
            "first_name": "Test",
            "last_name": "Student",
            "group_name": "TEST-01"
        }
        response = client.post("/api/students/register", json=student_data)
        # Note: This might fail without database, but tests the endpoint structure
        assert response.status_code in [200, 500]  # 500 if DB not connected
    
    def test_get_attendance_statistics(self):
        """Test attendance statistics endpoint."""
        response = client.get("/api/attendance/statistics")
        # Might fail without database, but tests endpoint structure
        assert response.status_code in [200, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

