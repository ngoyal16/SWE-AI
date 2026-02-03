import { useAIProfile } from "@/context/ai-profile-context";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Loader2, Sparkles } from "lucide-react";
import { type AIProfile } from "@/api/ai-profile";

export function AIProfileSelector() {
    const { profiles, selectedProfileId, setSelectedProfileId, isLoading } = useAIProfile();

    if (isLoading && profiles.length === 0) {
        return (
            <div className="flex items-center gap-2 px-3 h-9 rounded-md border border-input bg-background/50 text-muted-foreground text-xs animate-pulse">
                <Loader2 className="h-3 w-3 animate-spin" />
                <span>Loading AI profiles...</span>
            </div>
        );
    }

    return (
        <div className="flex items-center gap-2">
            <Select value={selectedProfileId} onValueChange={setSelectedProfileId}>
                <SelectTrigger className="w-[180px] h-9 bg-background/50 border-border/40 hover:bg-muted/50 transition-colors">
                    <div className="flex items-center gap-2 truncate">
                        <Sparkles className="h-3.5 w-3.5 text-primary shrink-0" />
                        <SelectValue placeholder="AI Profile" />
                    </div>
                </SelectTrigger>
                <SelectContent align="end" className="w-[220px]">
                    {profiles.map((profile: AIProfile) => (
                        <SelectItem key={profile.id} value={profile.id.toString()}>
                            <div className="flex flex-col gap-0.5 py-0.5">
                                <span className="text-sm font-medium leading-none">{profile.name}</span>
                                <span className="text-[10px] text-muted-foreground leading-none capitalize">
                                    {profile.provider} • {profile.default_model}
                                </span>
                            </div>
                        </SelectItem>
                    ))}
                    {profiles.length === 0 && (
                        <div className="p-2 text-center text-xs text-muted-foreground italic">
                            No profiles found
                        </div>
                    )}
                </SelectContent>
            </Select>
        </div>
    );
}
