# MEDIQR Mobile App

React Native mobile application for MEDIQR Pharmacy Management System using Expo.

## Overview

The MEDIQR mobile app provides a native mobile experience for both patients and pharmacists, complementing the existing web application. It integrates with the FastAPI backend to provide full functionality on mobile devices.

## Features

### Patient Features
- **QR Code Scanning**: Scan medicine QR codes from pharmacy bills
- **Medicine Details**: View comprehensive medicine information
- **Drug Interaction Checking**: Real-time interaction alerts using Neo4j
- **Medication Reminders**: Set and manage medication reminders
- **Medicine Information**: Access detailed drug information and side effects

### Pharmacist Features
- **Inventory Management**: View and manage medicine stock
- **Alternative Recommendations**: Get alternative medicine suggestions via Neo4j
- **Billing System**: Create bills and generate QR receipts
- **Drug Interaction Alerts**: Check interactions before dispensing
- **Analytics Dashboard**: View inventory and sales analytics

## Technology Stack

- **React Native**: Mobile framework
- **Expo**: Development and build tooling
- **React Navigation**: Screen navigation
- **Axios**: HTTP client for API calls
- **Expo Camera**: QR code scanning
- **Expo Notifications**: Push notifications for reminders
- **Async Storage**: Local data persistence

## Prerequisites

- Node.js (v16 or higher)
- npm or yarn
- Expo CLI
- iOS Simulator (for iOS development) or Android Emulator
- Physical iOS/Android device (for testing)
- MEDIQR backend running on accessible URL

## Installation

1. **Install Dependencies**
```bash
cd mobile
npm install
```

2. **Configure API URL**
Edit `src/config/api.js` and set your backend URL:
```javascript
const API_CONFIG = {
  BASE_URL: 'http://YOUR_BACKEND_IP:8000', // Change this to your backend URL
  TIMEOUT: 10000,
};
```

3. **Start Development Server**
```bash
npm start
```

4. **Run on Device/Simulator**
- Press `i` for iOS Simulator
- Press `a` for Android Emulator
- Scan QR code with Expo Go app for physical device

## Project Structure

```
mobile/
├── App.js                          # Main app component and navigation
├── app.json                        # Expo configuration
├── package.json                    # Dependencies
├── babel.config.js                 # Babel configuration
├── src/
│   ├── config/
│   │   └── api.js                  # API configuration
│   ├── services/
│   │   └── api.js                  # API service layer
│   └── screens/
│       ├── auth/
│       │   ├── LoginScreen.js      # Login screen
│       │   └── RegisterScreen.js   # Registration screen
│       ├── patient/
│       │   ├── PatientDashboard.js      # Patient home
│       │   ├── ScannerScreen.js         # QR scanner
│       │   ├── MedicineDetailsScreen.js # Medicine info
│       │   └── RemindersScreen.js       # Reminders management
│       └── pharmacist/
│           ├── PharmacistDashboard.js    # Pharmacist home
│           ├── InventoryScreen.js        # Inventory management
│           └── BillingScreen.js          # Billing system
```

## API Integration

The mobile app uses the same FastAPI backend as the web application. All API calls are handled through the `src/services/api.js` file.

### Available API Services

- **authAPI**: Login, register
- **patientAPI**: Get bill details, manage reminders
- **pharmacistAPI**: Inventory management, billing
- **medicineGraphAPI**: Drug interactions, alternatives (Neo4j)

## Usage

### For Patients

1. **Login/Register**: Create account or login with existing credentials
2. **Scan QR Code**: Use the scanner to read medicine QR codes from bills
3. **View Medicine Details**: See detailed information about medicines
4. **Set Reminders**: Create medication reminders
5. **Check Interactions**: View drug-drug interaction warnings

### For Pharmacists

1. **Login/Register**: Access pharmacist dashboard
2. **Manage Inventory**: Add medicines, view stock levels
3. **Create Bills**: Generate bills with automatic QR code generation
4. **Check Interactions**: Verify drug interactions before dispensing
5. **View Alternatives**: Get alternative medicine recommendations

## Configuration

### Camera Permissions

The app requires camera permissions for QR scanning. These are configured in `app.json`:

```json
{
  "plugins": [
    ["expo-camera", {
      "cameraPermission": "Allow $(PRODUCT_NAME) to access your camera"
    }]
  ]
}
```

### Backend URL

Update the backend URL in `src/config/api.js` to point to your running FastAPI server:

```javascript
const API_CONFIG = {
  BASE_URL: 'http://192.168.1.100:8000', // Use your local IP for device testing
  TIMEOUT: 10000,
};
```

**Note**: When testing on physical devices, use your computer's local IP address instead of `localhost`.

## Building for Production

### iOS

1. **Install EAS CLI**
```bash
npm install -g eas-cli
```

2. **Configure EAS**
```bash
eas build:configure
```

3. **Build**
```bash
eas build --platform ios
```

### Android

1. **Build APK**
```bash
eas build --platform android --profile preview
```

2. **Build for Play Store**
```bash
eas build --platform android
```

## Troubleshooting

### Metro Bundler Issues
If you encounter Metro bundler issues:
```bash
npm start -- --clear
```

### Cache Issues
Clear the cache:
```bash
rm -rf node_modules
npm install
npx expo start -c
```

### Network Issues
- Ensure your backend is accessible from your device
- Use your computer's local IP address instead of localhost
- Check firewall settings

### Camera Issues
- Ensure camera permissions are granted
- Check if camera is being used by another app
- Try restarting the app

## Development Tips

1. **Hot Reloading**: The app supports hot reloading for faster development
2. **Debugging**: Use React Native Debugger or Expo's built-in debugging tools
3. **Testing**: Test on both iOS and Android platforms
4. **API Testing**: Use the existing backend API documentation for reference

## Security Considerations

- API tokens are stored securely using AsyncStorage
- HTTPS should be used in production
- Sensitive data should be encrypted
- Implement proper authentication flow

## Future Enhancements

- [ ] Push notifications for medication reminders
- [ ] Offline mode for basic functionality
- [ ] Biometric authentication
- [ ] Prescription OCR
- [ ] Voice-based medicine guidance
- [ ] Multi-language support

## Contributing

When contributing to the mobile app:
1. Follow the existing code style
2. Test on both iOS and Android
3. Update documentation as needed
4. Ensure API compatibility with backend

## Support

For issues or questions:
- Check the main project README
- Review FastAPI backend documentation
- Check Expo documentation for platform-specific issues

## License

This mobile app is part of the MEDIQR project and follows the same license terms.
