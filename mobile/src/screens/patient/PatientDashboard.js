import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

const PatientDashboard = ({ navigation }) => {
  const handleLogout = async () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: async () => {
            await AsyncStorage.removeItem('authToken');
            await AsyncStorage.removeItem('user');
            navigation.reset({
              index: 0,
              routes: [{ name: 'Login' }],
            });
          },
        },
      ]
    );
  };

  const features = [
    {
      id: 1,
      title: 'Scan QR Code',
      description: 'Scan medicine QR codes to view details',
      icon: '📷',
      screen: 'Scanner',
      color: '#4CAF50',
    },
    {
      id: 2,
      title: 'My Reminders',
      description: 'Manage your medication reminders',
      icon: '⏰',
      screen: 'Reminders',
      color: '#2196F3',
    },
    {
      id: 3,
      title: 'Medicine Info',
      description: 'Learn about your medicines',
      icon: '💊',
      screen: 'MedicineDetails',
      color: '#FF9800',
    },
  ];

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Patient Dashboard</Text>
        <Text style={styles.subtitle}>Welcome to MEDIQR</Text>
      </View>

      <View style={styles.featuresContainer}>
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        {features.map((feature) => (
          <TouchableOpacity
            key={feature.id}
            style={[styles.featureCard, { borderLeftColor: feature.color }]}
            onPress={() => navigation.navigate(feature.screen)}
          >
            <View style={styles.featureIconContainer}>
              <Text style={styles.featureIcon}>{feature.icon}</Text>
            </View>
            <View style={styles.featureInfo}>
              <Text style={styles.featureTitle}>{feature.title}</Text>
              <Text style={styles.featureDescription}>{feature.description}</Text>
            </View>
            <Text style={styles.arrow}>›</Text>
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.infoCard}>
        <Text style={styles.infoTitle}>How to use MEDIQR</Text>
        <Text style={styles.infoText}>
          1. Scan QR code from your pharmacy bill
        </Text>
        <Text style={styles.infoText}>
          2. View detailed medicine information
        </Text>
        <Text style={styles.infoText}>
          3. Set reminders for your medications
        </Text>
        <Text style={styles.infoText}>
          4. Check for drug interactions
        </Text>
      </View>

      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Text style={styles.logoutButtonText}>Logout</Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#4CAF50',
    padding: 30,
    paddingTop: 50,
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 5,
  },
  subtitle: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.9)',
  },
  featuresContainer: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  featureCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 15,
    marginBottom: 15,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    borderLeftWidth: 4,
  },
  featureIconContainer: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#f5f5f5',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 15,
  },
  featureIcon: {
    fontSize: 24,
  },
  featureInfo: {
    flex: 1,
  },
  featureTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 3,
  },
  featureDescription: {
    fontSize: 13,
    color: '#666',
  },
  arrow: {
    fontSize: 24,
    color: '#ccc',
    fontWeight: 'bold',
  },
  infoCard: {
    backgroundColor: '#fff',
    margin: 20,
    marginTop: 0,
    borderRadius: 12,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  infoTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  infoText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
    lineHeight: 20,
  },
  logoutButton: {
    backgroundColor: '#f44336',
    margin: 20,
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    marginBottom: 30,
  },
  logoutButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default PatientDashboard;
