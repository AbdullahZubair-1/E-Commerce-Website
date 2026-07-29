import api from './api';
import type { APIResponse } from '@/types';

export interface Doctor {
  id: string;
  name: string;
  specialty: string | null;
  cal_event_type_id: string;
  is_active: boolean;
}

export interface Appointment {
  id: string;
  doctor_id: string;
  doctor_name: string;
  customer_name: string;
  customer_email: string;
  customer_phone: string | null;
  scheduled_at: string;
  status: string;
  created_at: string;
}

export const appointmentService = {
  async listDoctors(): Promise<Doctor[]> {
    const res = await api.get<APIResponse<Doctor[]>>('/appointments/admin/doctors');
    return res.data.data!;
  },

  async createDoctor(name: string, cal_event_type_id: string, specialty?: string): Promise<Doctor> {
    const res = await api.post<APIResponse<Doctor>>('/appointments/admin/doctors', {
      name,
      cal_event_type_id,
      specialty: specialty || undefined,
    });
    return res.data.data!;
  },

  async updateDoctor(id: string, updates: Partial<Pick<Doctor, 'name' | 'specialty' | 'cal_event_type_id' | 'is_active'>>): Promise<Doctor> {
    const res = await api.put<APIResponse<Doctor>>(`/appointments/admin/doctors/${id}`, updates);
    return res.data.data!;
  },

  async listAppointments(): Promise<Appointment[]> {
    const res = await api.get<APIResponse<Appointment[]>>('/appointments/admin/list');
    return res.data.data!;
  },
};