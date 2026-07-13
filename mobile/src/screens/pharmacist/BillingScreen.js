import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  Modal,
} from 'react-native';
import { pharmacistAPI, medicineGraphAPI } from '../../services/api';

const BillingScreen = ({ navigation }) => {
  const [billItems, setBillItems] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showMedicineModal, setShowMedicineModal] = useState(false);
  const [newItem, setNewItem] = useState({
    medicine_id: '',
    medicine_name: '',
    quantity: 1,
  });
  const [patientInfo, setPatientInfo] = useState({
    patient_name: '',
    patient_phone: '',
  });
  const [availableMedicines, setAvailableMedicines] = useState([]);
  const [interactions, setInteractions] = useState(null);

  const handleAddToBill = () => {
    if (!newItem.medicine_name || newItem.quantity < 1) {
      Alert.alert('Error', 'Please fill in medicine details');
      return;
    }

    setBillItems([...billItems, { ...newItem }]);
    setNewItem({
      medicine_id: '',
      medicine_name: '',
      quantity: 1,
    });
    setShowAddModal(false);
    checkInteractions();
  };

  const checkInteractions = async () => {
    if (billItems.length < 2) return;

    try {
      const medicineIds = billItems.map(item => item.medicine_id).filter(id => id);
      if (medicineIds.length >= 2) {
        const interactionData = await medicineGraphAPI.checkDrugInteractions(medicineIds);
        setInteractions(interactionData);
        
        if (interactionData.has_interactions) {
          Alert.alert(
            'Drug Interactions Found',
            `${interactionData.total_interactions} interaction(s) detected. Please review before proceeding.`,
            [{ text: 'OK' }]
          );
        }
      }
    } catch (error) {
      console.error('Failed to check interactions:', error);
    }
  };

  const handleRemoveItem = (index) => {
    const updatedItems = billItems.filter((_, i) => i !== index);
    setBillItems(updatedItems);
    checkInteractions();
  };

  const handleCreateBill = async () => {
    if (billItems.length === 0) {
      Alert.alert('Error', 'Please add at least one medicine');
      return;
    }

    if (!patientInfo.patient_name) {
      Alert.alert('Error', 'Please enter patient name');
      return;
    }

    try {
      const billData = {
        patient_name: patientInfo.patient_name,
        patient_phone: patientInfo.patient_phone,
        items: billItems,
      };

      const response = await pharmacistAPI.createBill(billData);
      const invoiceNumber = response.data?.invoice_number || response.invoice_number || 'N/A';
      
      Alert.alert(
        'Success',
        `Bill created successfully! Bill Number: ${invoiceNumber}`,
        [
          {
            text: 'OK',
            onPress: () => {
              setBillItems([]);
              setPatientInfo({ patient_name: '', patient_phone: '' });
              setInteractions(null);
              navigation.goBack();
            },
          },
        ]
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to create bill');
    }
  };

  const calculateTotal = () => {
    return billItems.reduce((total, item) => total + (item.quantity * (item.price || 0)), 0);
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Create Bill</Text>
      </View>

      <ScrollView style={styles.scrollView}>
        {/* Patient Information */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Patient Information</Text>
          <TextInput
            style={styles.input}
            placeholder="Patient Name *"
            value={patientInfo.patient_name}
            onChangeText={(text) => setPatientInfo({...patientInfo, patient_name: text})}
          />
          <TextInput
            style={styles.input}
            placeholder="Patient Phone"
            value={patientInfo.patient_phone}
            onChangeText={(text) => setPatientInfo({...patientInfo, patient_phone: text})}
            keyboardType="phone-pad"
          />
        </View>

        {/* Bill Items */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Bill Items</Text>
            <TouchableOpacity
              style={styles.addButton}
              onPress={() => setShowAddModal(true)}
            >
              <Text style={styles.addButtonText}>+ Add Medicine</Text>
            </TouchableOpacity>
          </View>

          {billItems.length === 0 ? (
            <Text style={styles.emptyText}>No medicines added yet</Text>
          ) : (
            billItems.map((item, index) => (
              <View key={index} style={styles.billItem}>
                <View style={styles.itemInfo}>
                  <Text style={styles.itemName}>{item.medicine_name}</Text>
                  <Text style={styles.itemDetails}>
                    Qty: {item.quantity} × ${item.price || '0.00'} = ${((item.quantity || 0) * (item.price || 0)).toFixed(2)}
                  </Text>
                </View>
                <TouchableOpacity
                  style={styles.removeButton}
                  onPress={() => handleRemoveItem(index)}
                >
                  <Text style={styles.removeButtonText}>×</Text>
                </TouchableOpacity>
              </View>
            ))
          )}
        </View>

        {/* Drug Interactions Warning */}
        {interactions && interactions.has_interactions && (
          <View style={styles.warningCard}>
            <Text style={styles.warningTitle}>⚠️ Drug Interactions</Text>
            {interactions.interactions.slice(0, 2).map((interaction, index) => (
              <Text key={index} style={styles.warningText}>
                • {interaction.medicine_1.name} ↔ {interaction.medicine_2.name} ({interaction.severity})
              </Text>
            ))}
            {interactions.total_interactions > 2 && (
              <Text style={styles.warningText}>
                • +{interactions.total_interactions - 2} more interactions
              </Text>
            )}
          </View>
        )}

        {/* Total */}
        <View style={styles.totalCard}>
          <Text style={styles.totalLabel}>Total Amount</Text>
          <Text style={styles.totalAmount}>${calculateTotal().toFixed(2)}</Text>
        </View>

        <TouchableOpacity style={styles.createButton} onPress={handleCreateBill}>
          <Text style={styles.createButtonText}>Create Bill & Generate QR</Text>
        </TouchableOpacity>
      </ScrollView>

      {/* Add Medicine Modal */}
      <Modal
        visible={showAddModal}
        animationType="slide"
        transparent={true}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Add Medicine to Bill</Text>
            
            <TextInput
              style={styles.input}
              placeholder="Medicine Name"
              value={newItem.medicine_name}
              onChangeText={(text) => setNewItem({...newItem, medicine_name: text})}
            />

            <TextInput
              style={styles.input}
              placeholder="Medicine ID (optional)"
              value={newItem.medicine_id}
              onChangeText={(text) => setNewItem({...newItem, medicine_id: text})}
            />

            <TextInput
              style={styles.input}
              placeholder="Price per Unit"
              value={newItem.price ? newItem.price.toString() : ''}
              onChangeText={(text) => setNewItem({...newItem, price: parseFloat(text) || 0})}
              keyboardType="decimal-pad"
            />

            <Text style={styles.label}>Quantity:</Text>
            <View style={styles.quantityContainer}>
              <TouchableOpacity
                style={styles.quantityButton}
                onPress={() => setNewItem({...newItem, quantity: Math.max(1, newItem.quantity - 1)})}
              >
                <Text style={styles.quantityButtonText}>-</Text>
              </TouchableOpacity>
              <Text style={styles.quantityText}>{newItem.quantity}</Text>
              <TouchableOpacity
                style={styles.quantityButton}
                onPress={() => setNewItem({...newItem, quantity: newItem.quantity + 1})}
              >
                <Text style={styles.quantityButtonText}>+</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={[styles.modalButton, styles.cancelButton]}
                onPress={() => setShowAddModal(false)}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.confirmButton]}
                onPress={handleAddToBill}
              >
                <Text style={styles.confirmButtonText}>Add to Bill</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#2196F3',
    padding: 20,
    paddingTop: 50,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  scrollView: {
    flex: 1,
    padding: 15,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 15,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    marginBottom: 10,
    fontSize: 16,
  },
  addButton: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 15,
  },
  addButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  emptyText: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
    paddingVertical: 20,
  },
  billItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  itemInfo: {
    flex: 1,
  },
  itemName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 3,
  },
  itemDetails: {
    fontSize: 14,
    color: '#666',
  },
  removeButton: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: '#f44336',
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 10,
  },
  removeButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  warningCard: {
    backgroundColor: '#fff3cd',
    borderRadius: 12,
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
  warningText: {
    fontSize: 14,
    color: '#856404',
    marginBottom: 5,
  },
  totalCard: {
    backgroundColor: '#4CAF50',
    borderRadius: 12,
    padding: 20,
    marginBottom: 15,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  totalLabel: {
    fontSize: 18,
    color: '#fff',
  },
  totalAmount: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  createButton: {
    backgroundColor: '#2196F3',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    marginBottom: 30,
  },
  createButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    padding: 20,
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 20,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 20,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 10,
  },
  quantityContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },
  quantityButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#2196F3',
    justifyContent: 'center',
    alignItems: 'center',
  },
  quantityButtonText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
  },
  quantityText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginHorizontal: 20,
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  modalButton: {
    flex: 1,
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginLeft: 10,
  },
  cancelButton: {
    backgroundColor: '#f5f5f5',
  },
  confirmButton: {
    backgroundColor: '#4CAF50',
  },
  cancelButtonText: {
    color: '#666',
    fontSize: 16,
    fontWeight: 'bold',
  },
  confirmButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default BillingScreen;
