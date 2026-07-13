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

const PharmacistDashboard = ({ navigation }) => {
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
      title: 'Inventory Management',
      description: 'Manage medicine stock and inventory',
      icon: '📦',
      screen: 'Inventory',
      color: '#4CAF50',
    },
    {
      id: 2,
      title: 'Create Bill',
      description: 'Generate bills and QR receipts',
      icon: '🧾',
      screen: 'Billing',
      color: '#2196F3',
    },
    {
      id: 3,
      title: 'Drug Interactions',
      description: 'Check medicine interactions',
      icon: '⚠️',
      screen: 'MedicineDetails',
      color: '#FF9800',
    },
    {
      id: 4,
      title: 'Analytics',
      description: 'View sales and inventory analytics',
      icon: '📊',
      screen: 'Inventory',
      color: '#9C27B0',
    },
  ];

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Pharmacist Dashboard</Text>
        <Text style={styles.subtitle}>MEDIQR Pharmacy Management</Text>
      </View>

      <View style={styles.statsContainer}>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>156</Text>
          <Text style={styles.statLabel}>Medicines</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>23</Text>
          <Text style={styles.statLabel}>Low Stock</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>5</Text>
          <Text style={styles.statLabel}>Expiring Soon</Text>
        </View>
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

      <View style={styles.alertCard}>
        <Text style={styles.alertTitle}>⚠️ Alerts</Text>
        <View style={styles.alertItem}>
          <Text style={styles.alertText}>• 5 medicines expiring in 30 days</Text>
        </View>
        <View style={styles.alertItem}>
          <Text style={styles.alertText}>• 23 medicines below minimum stock</Text>
        </View>
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
    backgroundColor: '#2196F3',
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
  statsContainer: {
    flexDirection: 'row',
    padding: 20,
    justifyContent: 'space-between',
  },
  statCard: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 15,
    alignItems: 'center',
    marginHorizontal: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2196F3',
    marginBottom: 5,
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
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
  alertCard: {
    backgroundColor: '#fff3cd',
    margin: 20,
    marginTop: 0,
    borderRadius: 12,
    padding: 20,
    borderLeftWidth: 4,
    borderLeftColor: '#ffc107',
  },
  alertTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#856404',
    marginBottom: 10,
  },
  alertItem: {
    marginBottom: 5,
  },
  alertText: {
    fontSize: 14,
    color: '#856404',
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

export default PharmacistDashboard;
