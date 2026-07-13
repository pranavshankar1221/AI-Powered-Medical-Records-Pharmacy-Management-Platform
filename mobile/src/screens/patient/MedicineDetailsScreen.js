import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { medicineGraphAPI } from '../../services/api';

const MedicineDetailsScreen = ({ route, navigation }) => {
  const { billData, token } = route.params;
  const [medicineDetails, setMedicineDetails] = useState(null);
  const [interactions, setInteractions] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMedicineDetails();
  }, [billData]);

  const loadMedicineDetails = async () => {
    try {
      setLoading(true);
      
      // Get medicine IDs from bill data
      const medicineIds = billData.items.map(item => item.medicine_id);
      
      // Fetch detailed medicine information from Neo4j
      if (medicineIds.length > 0) {
        const details = await medicineGraphAPI.getMedicineDetails(medicineIds[0]);
        setMedicineDetails(details);
        
        // Check for interactions
        const interactionData = await medicineGraphAPI.checkDrugInteractions(medicineIds);
        setInteractions(interactionData);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to load medicine details');
    } finally {
      setLoading(false);
    }
  };

  const handleSetReminder = (medicine) => {
    navigation.navigate('Reminders', {
      medicine: medicine,
      billToken: token,
    });
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#4CAF50" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Bill Information</Text>
        <View style={styles.row}>
          <Text style={styles.label}>Bill Number:</Text>
          <Text style={styles.value}>{billData.invoice_number || billData.bill_number}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>Patient:</Text>
          <Text style={styles.value}>{billData.patient_name}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>Total Amount:</Text>
          <Text style={styles.value}>${billData.final_amount !== undefined ? billData.final_amount : billData.total_amount}</Text>
        </View>
      </View>

      <Text style={styles.sectionTitle}>Medicines</Text>
      {billData.items.map((item, index) => (
        <View key={index} style={styles.card}>
          <Text style={styles.medicineName}>{item.medicine_name}</Text>
          <View style={styles.row}>
            <Text style={styles.label}>Quantity:</Text>
            <Text style={styles.value}>{item.quantity}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>Price:</Text>
            <Text style={styles.value}>${item.unit_price}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>Subtotal:</Text>
            <Text style={styles.value}>${item.subtotal}</Text>
          </View>
          
          {medicineDetails && (
            <View style={styles.detailsSection}>
              <Text style={styles.detailsTitle}>Medicine Information</Text>
              <Text style={styles.detailsText}>
                <Text style={styles.detailsLabel}>Purpose:</Text> {medicineDetails.description || 'N/A'}
              </Text>
              <Text style={styles.detailsText}>
                <Text style={styles.detailsLabel}>Dosage:</Text> {medicineDetails.dosage_schedule || 'As prescribed'}
              </Text>
              <Text style={styles.detailsText}>
                <Text style={styles.detailsLabel}>Side Effects:</Text> {medicineDetails.side_effects || 'None listed'}
              </Text>
            </View>
          )}

          <TouchableOpacity
            style={styles.reminderButton}
            onPress={() => handleSetReminder(item)}
          >
            <Text style={styles.reminderButtonText}>Set Reminder</Text>
          </TouchableOpacity>
        </View>
      ))}

      {interactions && interactions.has_interactions && (
        <View style={styles.warningCard}>
          <Text style={styles.warningTitle}>⚠️ Drug Interactions Found</Text>
          {interactions.interactions.map((interaction, index) => (
            <View key={index} style={styles.interactionItem}>
              <Text style={styles.interactionText}>
                {interaction.medicine_1.name} ↔ {interaction.medicine_2.name}
              </Text>
              <Text style={styles.severityText}>
                Severity: {interaction.severity.toUpperCase()}
              </Text>
              <Text style={styles.descriptionText}>{interaction.description}</Text>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 15,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 15,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  label: {
    fontSize: 14,
    color: '#666',
  },
  value: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
    marginTop: 10,
  },
  medicineName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#4CAF50',
    marginBottom: 10,
  },
  detailsSection: {
    marginTop: 15,
    paddingTop: 15,
    borderTopWidth: 1,
    borderTopColor: '#eee',
  },
  detailsTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  detailsText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
    lineHeight: 20,
  },
  detailsLabel: {
    fontWeight: '600',
    color: '#333',
  },
  reminderButton: {
    backgroundColor: '#4CAF50',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 15,
  },
  reminderButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  warningCard: {
    backgroundColor: '#fff3cd',
    borderRadius: 10,
    padding: 15,
    marginBottom: 15,
    borderLeftWidth: 4,
    borderLeftColor: '#ffc107',
  },
  warningTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#856404',
    marginBottom: 10,
  },
  interactionItem: {
    marginBottom: 10,
    paddingBottom: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#ffeeba',
  },
  interactionText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 5,
  },
  severityText: {
    fontSize: 12,
    color: '#dc3545',
    marginBottom: 5,
  },
  descriptionText: {
    fontSize: 13,
    color: '#666',
    lineHeight: 18,
  },
});

export default MedicineDetailsScreen;
