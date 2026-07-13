import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  Modal,
} from 'react-native';
import { pharmacistAPI, medicineGraphAPI } from '../../services/api';

const InventoryScreen = ({ navigation }) => {
  const [medicines, setMedicines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedMedicine, setSelectedMedicine] = useState(null);
  const [showAlternativesModal, setShowAlternativesModal] = useState(false);
  const [alternatives, setAlternatives] = useState(null);
  const [newMedicine, setNewMedicine] = useState({
    medicine_name: '',
    generic_name: '',
    category: '',
    quantity: '',
    price_per_unit: '',
    expiry_date: '',
  });

  useEffect(() => {
    loadInventory();
  }, []);

  const loadInventory = async () => {
    try {
      setLoading(true);
      const response = await pharmacistAPI.getInventory();
      setMedicines(response.data || response.medicines || []);
    } catch (error) {
      Alert.alert('Error', 'Failed to load inventory');
    } finally {
      setLoading(false);
    }
  };

  const handleAddMedicine = async () => {
    if (!newMedicine.medicine_name || !newMedicine.quantity || !newMedicine.price_per_unit) {
      Alert.alert('Error', 'Please fill in required fields');
      return;
    }

    try {
      await pharmacistAPI.addMedicine({
        ...newMedicine,
        quantity: parseInt(newMedicine.quantity),
        price_per_unit: parseFloat(newMedicine.price_per_unit),
      });
      Alert.alert('Success', 'Medicine added successfully');
      setShowAddModal(false);
      setNewMedicine({
        medicine_name: '',
        generic_name: '',
        category: '',
        quantity: '',
        price_per_unit: '',
        expiry_date: '',
      });
      loadInventory();
    } catch (error) {
      Alert.alert('Error', 'Failed to add medicine');
    }
  };

  const handleShowAlternatives = async (medicine) => {
    try {
      setSelectedMedicine(medicine);
      const response = await medicineGraphAPI.getAlternatives(medicine.medicine_id);
      setAlternatives(response);
      setShowAlternativesModal(true);
    } catch (error) {
      Alert.alert('Error', 'Failed to load alternatives');
    }
  };

  const getStockStatus = (quantity) => {
    if (quantity <= 10) return { status: 'Low', color: '#f44336' };
    if (quantity <= 30) return { status: 'Medium', color: '#ff9800' };
    return { status: 'Good', color: '#4caf50' };
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#2196F3" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Inventory Management</Text>
        <TouchableOpacity
          style={styles.addButton}
          onPress={() => setShowAddModal(true)}
        >
          <Text style={styles.addButtonText}>+ Add Medicine</Text>
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.scrollView}>
        {medicines.map((medicine) => {
          const qty = medicine.total_stock !== undefined ? medicine.total_stock : medicine.quantity;
          const name = medicine.name || medicine.medicine_name;
          const price = medicine.unit_price !== undefined ? medicine.unit_price : medicine.price_per_unit;
          const stockStatus = getStockStatus(qty);
          return (
            <View key={medicine.id} style={styles.medicineCard}>
              <View style={styles.medicineHeader}>
                <Text style={styles.medicineName}>{name}</Text>
                <View style={[styles.stockBadge, { backgroundColor: stockStatus.color }]}>
                  <Text style={styles.stockText}>{stockStatus.status}</Text>
                </View>
              </View>
              
              <View style={styles.medicineDetails}>
                <Text style={styles.detailText}>
                  <Text style={styles.detailLabel}>Stock:</Text> {qty}
                </Text>
                <Text style={styles.detailText}>
                  <Text style={styles.detailLabel}>Price:</Text> ${price}
                </Text>
                <Text style={styles.detailText}>
                  <Text style={styles.detailLabel}>Category:</Text> {medicine.category}
                </Text>
                <Text style={styles.detailText}>
                  <Text style={styles.detailLabel}>Expiry:</Text> {medicine.expiry_date || 'N/A'}
                </Text>
              </View>

              <TouchableOpacity
                style={styles.alternativesButton}
                onPress={() => handleShowAlternatives(medicine)}
              >
                <Text style={styles.alternativesButtonText}>View Alternatives</Text>
              </TouchableOpacity>
            </View>
          );
        })}
      </ScrollView>

      {/* Add Medicine Modal */}
      <Modal
        visible={showAddModal}
        animationType="slide"
        transparent={true}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Add New Medicine</Text>
            
            <TextInput
              style={styles.input}
              placeholder="Medicine Name *"
              value={newMedicine.medicine_name}
              onChangeText={(text) => setNewMedicine({...newMedicine, medicine_name: text})}
            />

            <TextInput
              style={styles.input}
              placeholder="Generic Name"
              value={newMedicine.generic_name}
              onChangeText={(text) => setNewMedicine({...newMedicine, generic_name: text})}
            />

            <TextInput
              style={styles.input}
              placeholder="Category"
              value={newMedicine.category}
              onChangeText={(text) => setNewMedicine({...newMedicine, category: text})}
            />

            <TextInput
              style={styles.input}
              placeholder="Quantity *"
              value={newMedicine.quantity}
              onChangeText={(text) => setNewMedicine({...newMedicine, quantity: text})}
              keyboardType="numeric"
            />

            <TextInput
              style={styles.input}
              placeholder="Price per Unit *"
              value={newMedicine.price_per_unit}
              onChangeText={(text) => setNewMedicine({...newMedicine, price_per_unit: text})}
              keyboardType="decimal-pad"
            />

            <TextInput
              style={styles.input}
              placeholder="Expiry Date (YYYY-MM-DD)"
              value={newMedicine.expiry_date}
              onChangeText={(text) => setNewMedicine({...newMedicine, expiry_date: text})}
            />

            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={[styles.modalButton, styles.cancelButton]}
                onPress={() => setShowAddModal(false)}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.confirmButton]}
                onPress={handleAddMedicine}
              >
                <Text style={styles.confirmButtonText}>Add Medicine</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Alternatives Modal */}
      <Modal
        visible={showAlternativesModal}
        animationType="slide"
        transparent={true}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Alternative Medicines</Text>
            
            {selectedMedicine && (
              <View style={styles.originalMedicine}>
                <Text style={styles.originalLabel}>Original:</Text>
                <Text style={styles.originalName}>{selectedMedicine.medicine_name}</Text>
              </View>
            )}

            <ScrollView style={styles.alternativesList}>
              {alternatives && alternatives.alternatives && alternatives.alternatives.length > 0 ? (
                alternatives.alternatives.map((alt, index) => (
                  <View key={index} style={styles.alternativeCard}>
                    <Text style={styles.altName}>{alt.name}</Text>
                    <Text style={styles.altType}>{alt.recommendation_type}</Text>
                    <Text style={styles.altReason}>{alt.reason}</Text>
                    <Text style={styles.altPrice}>Price: ${alt.price}</Text>
                  </View>
                ))
              ) : (
                <Text style={styles.noAlternatives}>No alternatives found</Text>
              )}
            </ScrollView>

            <TouchableOpacity
              style={styles.closeButton}
              onPress={() => setShowAlternativesModal(false)}
            >
              <Text style={styles.closeButtonText}>Close</Text>
            </TouchableOpacity>
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
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingTop: 50,
    backgroundColor: '#fff',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  addButton: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 20,
  },
  addButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  scrollView: {
    flex: 1,
    padding: 15,
  },
  medicineCard: {
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
  medicineHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  medicineName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    flex: 1,
  },
  stockBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  stockText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  medicineDetails: {
    marginBottom: 10,
  },
  detailText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 3,
  },
  detailLabel: {
    fontWeight: '600',
    color: '#333',
  },
  alternativesButton: {
    backgroundColor: '#2196F3',
    padding: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  alternativesButtonText: {
    color: '#fff',
    fontSize: 14,
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
    maxHeight: '80%',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 20,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    marginBottom: 15,
    fontSize: 16,
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
  originalMedicine: {
    backgroundColor: '#f5f5f5',
    padding: 10,
    borderRadius: 8,
    marginBottom: 15,
  },
  originalLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 3,
  },
  originalName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  alternativesList: {
    maxHeight: 300,
    marginBottom: 15,
  },
  alternativeCard: {
    backgroundColor: '#f9f9f9',
    padding: 12,
    borderRadius: 8,
    marginBottom: 10,
  },
  altName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  altType: {
    fontSize: 12,
    color: '#2196F3',
    marginBottom: 3,
  },
  altReason: {
    fontSize: 13,
    color: '#666',
    marginBottom: 3,
  },
  altPrice: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#4CAF50',
  },
  noAlternatives: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
    paddingVertical: 20,
  },
  closeButton: {
    backgroundColor: '#2196F3',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  closeButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default InventoryScreen;
