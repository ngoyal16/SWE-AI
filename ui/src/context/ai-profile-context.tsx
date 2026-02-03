import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { aiProfileApi, type AIProfile } from '@/api/ai-profile';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

interface AIProfileContextType {
    selectedProfileId: string;
    setSelectedProfileId: (id: string) => void;
    profiles: AIProfile[];
    isLoading: boolean;
    selectedProfile: AIProfile | undefined;
}

const AIProfileContext = createContext<AIProfileContextType | undefined>(undefined);

export function AIProfileProvider({ children }: { children: ReactNode }) {
    const [selectedProfileId, setSelectedProfileIdState] = useState<string>('');
    const queryClient = useQueryClient();

    const { data: profiles = [], isLoading } = useQuery({
        queryKey: ['ai-profiles'],
        queryFn: aiProfileApi.list,
    });

    const { data: preference } = useQuery({
        queryKey: ['user-ai-preference'],
        queryFn: aiProfileApi.getUserPreference,
    });

    const updatePreferenceMutation = useMutation({
        mutationFn: aiProfileApi.updateUserPreference,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['user-ai-preference'] });
            toast.success('AI profile updated');
        },
        onError: (error: Error) => {
            toast.error(error.message || 'Failed to update AI profile');
        }
    });

    useEffect(() => {
        let targetId = '';
        if (preference?.ai_profile_id) {
            targetId = preference.ai_profile_id.toString();
        } else if (profiles.length > 0) {
            const defaultProfile = profiles.find(p => p.is_default) || profiles[0];
            if (defaultProfile) {
                targetId = defaultProfile.id.toString();
            }
        }

        // Only update if we have a target and it's different, and we haven't manually set one yet (or we want to sync)
        // Here we assume if selectedProfileId is empty, we should fill it.
        // If preference changes, we might want to update it too.
        if (targetId && targetId !== selectedProfileId) {
             setSelectedProfileIdState(targetId);
        }
    }, [preference, profiles, selectedProfileId]);

    const setSelectedProfileId = (id: string) => {
        setSelectedProfileIdState(id);
        updatePreferenceMutation.mutate(parseInt(id));
    };

    const selectedProfile = profiles.find(p => p.id.toString() === selectedProfileId);

    return (
        <AIProfileContext.Provider value={{
            selectedProfileId,
            setSelectedProfileId,
            profiles: profiles.filter(p => p.is_enabled),
            isLoading,
            selectedProfile
        }}>
            {children}
        </AIProfileContext.Provider>
    );
}

export function useAIProfile() {
    const context = useContext(AIProfileContext);
    if (context === undefined) {
        throw new Error('useAIProfile must be used within an AIProfileProvider');
    }
    return context;
}
