import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';

// Screens
import LoginScreen from './src/screens/auth/LoginScreen';
import RegisterScreen from './src/screens/auth/RegisterScreen';
import PatientDashboard from './src/screens/patient/PatientDashboard';
import ScannerScreen from './src/screens/patient/ScannerScreen';
import MedicineDetailsScreen from './src/screens/patient/MedicineDetailsScreen';
import RemindersScreen from './src/screens/patient/RemindersScreen';
import PharmacistDashboard from './src/screens/pharmacist/PharmacistDashboard';
import InventoryScreen from './src/screens/pharmacist/InventoryScreen';
import BillingScreen from './src/screens/pharmacist/BillingScreen';

const Stack = createNativeStackNavigator();

export default function App() {
  return (
    <>
      <StatusBar style="auto" />
      <NavigationContainer>
        <Stack.Navigator initialRouteName="Login">
          <Stack.Screen 
            name="Login" 
            component={LoginScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="Register" 
            component={RegisterScreen}
            options={{ title: 'Create Account' }}
          />
          <Stack.Screen 
            name="PatientDashboard" 
            component={PatientDashboard}
            options={{ title: 'Patient Dashboard', headerLeft: null }}
          />
          <Stack.Screen 
            name="Scanner" 
            component={ScannerScreen}
            options={{ title: 'Scan QR Code' }}
          />
          <Stack.Screen 
            name="MedicineDetails" 
            component={MedicineDetailsScreen}
            options={{ title: 'Medicine Details' }}
          />
          <Stack.Screen 
            name="Reminders" 
            component={RemindersScreen}
            options={{ title: 'My Reminders' }}
          />
          <Stack.Screen 
            name="PharmacistDashboard" 
            component={PharmacistDashboard}
            options={{ title: 'Pharmacist Dashboard', headerLeft: null }}
          />
          <Stack.Screen 
            name="Inventory" 
            component={InventoryScreen}
            options={{ title: 'Inventory Management' }}
          />
          <Stack.Screen 
            name="Billing" 
            component={BillingScreen}
            options={{ title: 'Create Bill' }}
          />
        </Stack.Navigator>
      </NavigationContainer>
    </>
  );
}
