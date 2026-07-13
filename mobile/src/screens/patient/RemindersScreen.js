import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  TextInput,
  Modal,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { patientAPI } from '../../services/api';

const RemindersScreen = ({ route }) => {
  const { medicine, billToken } = route.params || {};
  const [reminders, setReminders] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newReminder, setNewReminder] = useState({
    medicine_id: medicine?.medicine_id || '',
    medicine_name: medicine?.medicine_name || '',
    reminder_time: '',
    reminder_type: 'morning',
  });

  useEffect(() => {
    loadReminders();
  }, []);

  const loadReminders = async () => {
    try {
      const response = await patientAPI.getReminders();
      setReminders(response.data || response.reminders || []);
    } catch (error) {
      console.error('Failed to load reminders:', error);
    }
  };

  const handleAddReminder = async () => {
    if (!newReminder.reminder_time) {
      Alert.alert('Error', 'Please set a reminder time');
      return;
    }

    try {
      await patientAPI.createReminder(newReminder);
      Alert.alert('Success', 'Reminder set successfully');
      setShowAddModal(false);
      loadReminders();
    } catch (error) {
      Alert.alert('Error', 'Failed to set reminder');
    }
  };

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView}>
        <View style={styles.header}>
          <Text style={styles.title}>My Reminders</Text>
          <TouchableOpacity
            style={styles.addButton}
            onPress={() => setShowAddModal(true)}
          >
            <Text style={styles.addButtonText}>+ Add Reminder</Text>
          </TouchableOpacity>
        </View>

        {reminders.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>No reminders set yet</Text>
            <Text style={styles.emptySubtext}>
              Tap "Add Reminder" to create your first medication reminder
            </Text>
          </View>
        ) : (
          reminders.map((reminder, index) => (
            <View key={index} style={styles.reminderCard}>
              <View style={styles.reminderHeader}>
                <Text style={styles.medicineName}>{reminder.medicine_name}</Text>
                <View style={[
                  styles.statusBadge,
                  reminder.status === 'active' || reminder.is_active ? styles.activeBadge : styles.completedBadge
                ]}>
                  <Text style={styles.statusText}>{reminder.status || (reminder.is_active ? 'active' : 'inactive')}</Text>
                </View>
              </View>
              
              <View style={styles.reminderDetails}>
                <Text style={styles.detailText}>
                  <Text style={styles.detailLabel}>Time:</Text> {reminder.custom_time || reminder.reminder_time || 'N/A'}
                </Text>
                <Text style={styles.detailText}>
                  <Text style={styles.detailLabel}>Type:</Text> {reminder.time_of_day || reminder.reminder_type || 'N/A'}
                </Text>
              </View>
            </View>
          ))
        )}
      </ScrollView>

      <Modal
        visible={showAddModal}
        animationType="slide"
        transparent={true}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Add New Reminder</Text>
            
            <TextInput
              style={styles.input}
              placeholder="Medicine Name"
              value={newReminder.medicine_name}
              onChangeText={(text) => setNewReminder({...newReminder, medicine_name: text})}
            />

            <TextInput
              style={styles.input}
              placeholder="Reminder Time (e.g., 08:00)"
              value={newReminder.reminder_time}
              onChangeText={(text) => setNewReminder({...newReminder, reminder_time: text})}
            />

            <Text style={styles.label}>Reminder Type:</Text>
            <View style={styles.typeContainer}>
              {['morning', 'afternoon', 'evening'].map((type) => (
                <TouchableOpacity
                  key={type}
                  style={[
                    styles.typeButton,
                    newReminder.reminder_type === type && styles.typeButtonActive
                  ]}
                  onPress={() => setNewReminder({...newReminder, reminder_type: type})}
                >
                  <Text style={[
                    styles.typeText,
                    newReminder.reminder_type === type && styles.typeTextActive
                  ]}>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </Text>
                </TouchableOpacity>
              ))}
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
                onPress={handleAddReminder}
              >
                <Text style={styles.confirmButtonText}>Set Reminder</Text>
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
  scrollView: {
    flex: 1,
    padding: 15,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
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
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 50,
  },
  emptyText: {
    fontSize: 18,
    color: '#999',
    marginBottom: 10,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#ccc',
    textAlign: 'center',
  },
  reminderCard: {
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
  reminderHeader: {
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
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  activeBadge: {
    backgroundColor: '#4CAF50',
  },
  completedBadge: {
    backgroundColor: '#9E9E9E',
  },
  statusText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  reminderDetails: {
    marginTop: 5,
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
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    marginBottom: 15,
    fontSize: 16,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 10,
  },
  typeContainer: {
    flexDirection: 'row',
    marginBottom: 20,
  },
  typeButton: {
    flex: 1,
    padding: 12,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    alignItems: 'center',
    marginRight: 10,
  },
  typeButtonActive: {
    backgroundColor: '#4CAF50',
    borderColor: '#4CAF50',
  },
  typeText: {
    fontSize: 14,
    color: '#666',
  },
  typeTextActive: {
    color: '#fff',
    fontWeight: 'bold',
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

export default RemindersScreen;
