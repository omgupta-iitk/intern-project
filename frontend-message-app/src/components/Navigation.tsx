import { Link } from 'react-router-dom';
import { SignedIn, SignedOut, SignInButton, SignOutButton, useUser } from '@clerk/clerk-react';
import '../styles/Navigation.css';

const Navigation = () => {
  const { user } = useUser();

  return (
    <nav className="navigation">
      <div className="nav-container">
        <div className="nav-logo">
          <Link to="/">MessageApp</Link>
        </div>
        
        <div className="nav-links">
          <SignedIn>
            <Link to="/" className="nav-link">Profile</Link>
            <Link to="/chat" className="nav-link">Messages</Link>
            
            <div className="user-menu">
              <span className="username">{user?.fullName || 'User'}</span>
              <SignOutButton>
                <button className="sign-out-button">Sign Out</button>
              </SignOutButton>
            </div>
          </SignedIn>
          
          <SignedOut>
            <SignInButton mode="modal">
              <button className="sign-in-button">Sign In</button>
            </SignInButton>
          </SignedOut>
        </div>
      </div>
    </nav>
  );
};

export default Navigation; 