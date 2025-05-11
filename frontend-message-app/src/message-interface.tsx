import { useAuth } from "@clerk/clerk-react";
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./styles/UserInfo.css";

interface UserData {
  id: string;
  fullName: string;
  phoneNumber: string;
  publicEmail: string;
}

interface FormData {
  fullName: string;
  phoneNumber: string;
  publicEmail: string;
}

export default function UserInfo() {
  const { getToken } = useAuth();
  const navigate = useNavigate();
  const [userData, setUserData] = useState<UserData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState<boolean>(false);
  const [formData, setFormData] = useState<FormData>({
    fullName: '',
    publicEmail: '',
    phoneNumber: ''
  });

  // Check if user exists on component mount
  useEffect(() => {
    const checkUserExists = async () => {
      setLoading(true);
      setError(null);
      try {
        const token = await getToken();
        const response = await fetch("http://localhost:8000/users/me", {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });

        if (response.ok) {
          const data: UserData = await response.json();
          setUserData(data);
        } else if (response.status === 400) {
          setShowForm(true);
        } else {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
      } catch (error) {
        setError(error instanceof Error ? error.message : 'An unknown error occurred');
      } finally {
        setLoading(false);
      }
    };

    checkUserExists();
  }, [getToken]);

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const response = await fetch("http://localhost:8000/create-user", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          ...formData
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: UserData = await response.json();
      setUserData(data);
      setShowForm(false);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'An unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const navigateToChat = () => {
    navigate('/chat');
  };

  return (
    <div className="user-info-page">
      <div className="card user-info-card">
        <h1 className="page-title">User Profile</h1>
        
        {loading && <div className="loading">Loading...</div>}
        {error && <div className="error-message">{error}</div>}

        {userData ? (
          <div className="profile-container">
            <div className="profile-header">
              <div className="profile-avatar">
                {userData.fullName.charAt(0).toUpperCase()}
              </div>
              <h2>{userData.fullName}</h2>
            </div>
            
            <div className="profile-details">
              <div className="detail-item">
                <span className="detail-label">Email:</span>
                <span className="detail-value">{userData.publicEmail}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Phone:</span>
                <span className="detail-value">{userData.phoneNumber}</span>
              </div>
            </div>
            
            <button 
              className="btn primary-button"
              onClick={navigateToChat}
            >
              Go to Messages
            </button>
          </div>
        ) : showForm ? (
          <div className="form-container">
            <form onSubmit={handleSubmit} className="profile-form">
              <h2>Complete Your Profile</h2>
              <p className="form-description">Please provide your information to get started</p>
              
              <div className="form-group">
                <label htmlFor="fullName">Full Name</label>
                <input
                  id="fullName"
                  type="text"
                  name="fullName"
                  value={formData.fullName}
                  onChange={handleInputChange}
                  placeholder="Enter your full name"
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="phoneNumber">Phone Number</label>
                <input
                  id="phoneNumber"
                  type="tel"
                  name="phoneNumber"
                  value={formData.phoneNumber}
                  onChange={handleInputChange}
                  placeholder="Enter your phone number"
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="publicEmail">Email Address</label>
                <input
                  id="publicEmail"
                  type="email"
                  name="publicEmail"
                  value={formData.publicEmail}
                  onChange={handleInputChange}
                  placeholder="Enter your email address"
                  required
                />
              </div>
              
              <button 
                type="submit" 
                className="btn submit-button" 
                disabled={loading}
              >
                {loading ? 'Submitting...' : 'Save Profile'}
              </button>
            </form>
          </div>
        ) : (
          <div className="loading">Checking user status...</div>
        )}
      </div>
    </div>
  );
}