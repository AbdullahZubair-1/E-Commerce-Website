import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import toast from 'react-hot-toast';
import { UserIcon, KeyIcon } from '@heroicons/react/24/outline';
import { useAuth } from '@/hooks/useAuth';
import { userService } from '@/services/user.service';
import { getErrorMessage } from '@/services/api';
import { formatDate } from '@/utils/format';

const profileSchema = z.object({
  first_name: z.string().min(2, 'First name must be at least 2 characters'),
  last_name: z.string().min(2, 'Last name must be at least 2 characters'),
});

const passwordSchema = z.object({
  current_password: z.string().min(1, 'Current password is required'),
  new_password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Must contain an uppercase letter')
    .regex(/[a-z]/, 'Must contain a lowercase letter')
    .regex(/\d/, 'Must contain a digit'),
  confirm_password: z.string(),
}).refine((d) => d.new_password === d.confirm_password, {
  message: 'Passwords do not match',
  path: ['confirm_password'],
});

type ProfileFormData = z.infer<typeof profileSchema>;
type PasswordFormData = z.infer<typeof passwordSchema>;

export function ProfilePage() {
  const { user, setUser } = useAuth();
  const [activeTab, setActiveTab] = useState<'profile' | 'password'>('profile');

  const profileForm = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: { first_name: user?.first_name ?? '', last_name: user?.last_name ?? '' },
  });

  const passwordForm = useForm<PasswordFormData>({
    resolver: zodResolver(passwordSchema),
  });

  const onProfileSubmit = async (data: ProfileFormData) => {
    try {
      const updated = await userService.updateProfile(data.first_name, data.last_name);
      setUser(updated);
      toast.success('Profile updated.');
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  const onPasswordSubmit = async (data: PasswordFormData) => {
    try {
      await userService.changePassword(data.current_password, data.new_password);
      passwordForm.reset();
      toast.success('Password changed successfully.');
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">My Profile</h1>

      {/* User info card */}
      <div className="card p-6 mb-6 flex items-center gap-4">
        <div className="h-16 w-16 rounded-full bg-orange-100 flex items-center justify-center flex-shrink-0">
          <span className="text-2xl font-bold text-orange-600">
            {user?.first_name?.[0]}{user?.last_name?.[0]}
          </span>
        </div>
        <div>
          <h2 className="text-xl font-semibold">{user?.first_name} {user?.last_name}</h2>
          <p className="text-gray-500 text-sm">{user?.email}</p>
          <p className="text-xs text-gray-400 mt-1">Member since {user ? formatDate(user.created_at) : '—'}</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-6" role="tablist">
        <button
          role="tab"
          aria-selected={activeTab === 'profile'}
          onClick={() => setActiveTab('profile')}
          className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'profile'
              ? 'border-orange-600 text-orange-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <UserIcon className="h-4 w-4" aria-hidden="true" />
          Profile Info
        </button>
        <button
          role="tab"
          aria-selected={activeTab === 'password'}
          onClick={() => setActiveTab('password')}
          className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'password'
              ? 'border-orange-600 text-orange-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <KeyIcon className="h-4 w-4" aria-hidden="true" />
          Change Password
        </button>
      </div>

      {/* Profile form */}
      {activeTab === 'profile' && (
        <div className="card p-6">
          <form onSubmit={profileForm.handleSubmit(onProfileSubmit)} className="space-y-4" noValidate>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="first_name" className="block text-sm font-medium text-gray-700 mb-1">
                  First Name
                </label>
                <input
                  id="first_name"
                  type="text"
                  className="input-field"
                  {...profileForm.register('first_name')}
                  aria-invalid={!!profileForm.formState.errors.first_name}
                />
                {profileForm.formState.errors.first_name && (
                  <p className="text-red-500 text-xs mt-1" role="alert">
                    {profileForm.formState.errors.first_name.message}
                  </p>
                )}
              </div>
              <div>
                <label htmlFor="last_name" className="block text-sm font-medium text-gray-700 mb-1">
                  Last Name
                </label>
                <input
                  id="last_name"
                  type="text"
                  className="input-field"
                  {...profileForm.register('last_name')}
                  aria-invalid={!!profileForm.formState.errors.last_name}
                />
                {profileForm.formState.errors.last_name && (
                  <p className="text-red-500 text-xs mt-1" role="alert">
                    {profileForm.formState.errors.last_name.message}
                  </p>
                )}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input type="email" value={user?.email ?? ''} disabled className="input-field bg-gray-50 text-gray-400 cursor-not-allowed" />
              <p className="text-xs text-gray-400 mt-1">Email cannot be changed.</p>
            </div>
            <button
              type="submit"
              disabled={profileForm.formState.isSubmitting}
              className="btn-primary"
            >
              {profileForm.formState.isSubmitting ? 'Saving…' : 'Save Changes'}
            </button>
          </form>
        </div>
      )}

      {/* Password form */}
      {activeTab === 'password' && (
        <div className="card p-6">
          <form onSubmit={passwordForm.handleSubmit(onPasswordSubmit)} className="space-y-4" noValidate>
            <div>
              <label htmlFor="current_password" className="block text-sm font-medium text-gray-700 mb-1">
                Current Password
              </label>
              <input
                id="current_password"
                type="password"
                className="input-field"
                {...passwordForm.register('current_password')}
                aria-invalid={!!passwordForm.formState.errors.current_password}
              />
              {passwordForm.formState.errors.current_password && (
                <p className="text-red-500 text-xs mt-1" role="alert">
                  {passwordForm.formState.errors.current_password.message}
                </p>
              )}
            </div>
            <div>
              <label htmlFor="new_password" className="block text-sm font-medium text-gray-700 mb-1">
                New Password
              </label>
              <input
                id="new_password"
                type="password"
                className="input-field"
                {...passwordForm.register('new_password')}
                aria-invalid={!!passwordForm.formState.errors.new_password}
              />
              {passwordForm.formState.errors.new_password && (
                <p className="text-red-500 text-xs mt-1" role="alert">
                  {passwordForm.formState.errors.new_password.message}
                </p>
              )}
            </div>
            <div>
              <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700 mb-1">
                Confirm New Password
              </label>
              <input
                id="confirm_password"
                type="password"
                className="input-field"
                {...passwordForm.register('confirm_password')}
                aria-invalid={!!passwordForm.formState.errors.confirm_password}
              />
              {passwordForm.formState.errors.confirm_password && (
                <p className="text-red-500 text-xs mt-1" role="alert">
                  {passwordForm.formState.errors.confirm_password.message}
                </p>
              )}
            </div>
            <button
              type="submit"
              disabled={passwordForm.formState.isSubmitting}
              className="btn-primary"
            >
              {passwordForm.formState.isSubmitting ? 'Changing…' : 'Change Password'}
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
