import { useEffect, useState, useCallback } from 'react';
import { PlusIcon, UserGroupIcon, CalendarDaysIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { appointmentService, type Doctor, type Appointment } from '@/services/appointment.service';
import { getErrorMessage } from '@/services/api';
import { PageSpinner } from '@/components/ui/Spinner';

type Tab = 'doctors' | 'bookings';

export function AdminAppointmentsPage() {
  const [tab, setTab] = useState<Tab>('doctors');
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [name, setName] = useState('');
  const [specialty, setSpecialty] = useState('');
  const [eventTypeId, setEventTypeId] = useState('');

  const refresh = useCallback(async () => {
    try {
      const [d, a] = await Promise.all([
        appointmentService.listDoctors(),
        appointmentService.listAppointments(),
      ]);
      setDoctors(d);
      setAppointments(a);
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleAddDoctor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !eventTypeId.trim()) {
      toast.error('Name and Cal.com event type ID are required.');
      return;
    }
    setSubmitting(true);
    try {
      await appointmentService.createDoctor(name.trim(), eventTypeId.trim(), specialty.trim() || undefined);
      toast.success('Doctor added.');
      setName('');
      setSpecialty('');
      setEventTypeId('');
      setShowForm(false);
      refresh();
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleActive = async (doctor: Doctor) => {
    try {
      await appointmentService.updateDoctor(doctor.id, { is_active: !doctor.is_active });
      toast.success(doctor.is_active ? 'Doctor deactivated.' : 'Doctor activated.');
      refresh();
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  };

  if (loading) return <PageSpinner />;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Doctor Appointments</h1>
          <p className="text-sm text-gray-500 mt-1">Manage doctors and view bookings made through Ana.</p>
        </div>
        {tab === 'doctors' && (
          <button
            type="button"
            onClick={() => setShowForm((v) => !v)}
            className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700"
          >
            <PlusIcon className="h-4 w-4" />
            Add Doctor
          </button>
        )}
      </div>

      <div className="flex border-b border-gray-200 mb-6">
        <button
          type="button"
          onClick={() => setTab('doctors')}
          className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium ${tab === 'doctors' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
        >
          <UserGroupIcon className="h-4 w-4" />
          Doctors ({doctors.length})
        </button>
        <button
          type="button"
          onClick={() => setTab('bookings')}
          className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium ${tab === 'bookings' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
        >
          <CalendarDaysIcon className="h-4 w-4" />
          Bookings ({appointments.length})
        </button>
      </div>

      {tab === 'doctors' && (
        <>
          {showForm && (
            <form onSubmit={handleAddDoctor} className="bg-white rounded-2xl border border-gray-200 p-5 mb-6 space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Doctor name</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Dr. Ayesha Khan"
                    className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-400"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Specialty (optional)</label>
                  <input
                    type="text"
                    value={specialty}
                    onChange={(e) => setSpecialty(e.target.value)}
                    placeholder="General Physician"
                    className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-400"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Cal.com event type ID</label>
                  <input
                    type="text"
                    value={eventTypeId}
                    onChange={(e) => setEventTypeId(e.target.value)}
                    placeholder="123456"
                    className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-400"
                  />
                </div>
              </div>
              <p className="text-xs text-gray-400">
                Create an "event type" for this doctor in your Cal.com account first, then paste its ID here.
              </p>
              <button
                type="submit"
                disabled={submitting}
                className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {submitting ? 'Adding…' : 'Add Doctor'}
              </button>
            </form>
          )}

          {doctors.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-12">No doctors added yet.</p>
          ) : (
            <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-left text-xs font-semibold text-gray-500 uppercase">
                  <tr>
                    <th className="px-5 py-3">Name</th>
                    <th className="px-5 py-3">Specialty</th>
                    <th className="px-5 py-3">Cal.com Event Type</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {doctors.map((d) => (
                    <tr key={d.id}>
                      <td className="px-5 py-3 font-medium text-gray-900">{d.name}</td>
                      <td className="px-5 py-3 text-gray-600">{d.specialty || '—'}</td>
                      <td className="px-5 py-3 text-gray-500 font-mono text-xs">{d.cal_event_type_id}</td>
                      <td className="px-5 py-3">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${d.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                          {d.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-5 py-3 text-right">
                        <button
                          type="button"
                          onClick={() => handleToggleActive(d)}
                          className="text-xs text-blue-600 hover:text-blue-700"
                        >
                          {d.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {tab === 'bookings' && (
        appointments.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-12">No appointments booked yet.</p>
        ) : (
          <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left text-xs font-semibold text-gray-500 uppercase">
                <tr>
                  <th className="px-5 py-3">Customer</th>
                  <th className="px-5 py-3">Contact</th>
                  <th className="px-5 py-3">Doctor</th>
                  <th className="px-5 py-3">Scheduled</th>
                  <th className="px-5 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {appointments.map((a) => (
                  <tr key={a.id}>
                    <td className="px-5 py-3 font-medium text-gray-900">{a.customer_name}</td>
                    <td className="px-5 py-3 text-gray-500 text-xs">
                      <div>{a.customer_email}</div>
                      {a.customer_phone && <div>{a.customer_phone}</div>}
                    </td>
                    <td className="px-5 py-3 text-gray-600">{a.doctor_name}</td>
                    <td className="px-5 py-3 text-gray-600">{new Date(a.scheduled_at).toLocaleString()}</td>
                    <td className="px-5 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${a.status === 'booked' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-500'}`}>
                        {a.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}
    </div>
  );
}