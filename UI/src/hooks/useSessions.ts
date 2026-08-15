import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  type CreateSessionRequest,
  createSession,
  getPriceHistory,
  getSession,
  listSessions,
  startRun,
} from "../lib/apiClient";

export function useSessionList() {
  return useQuery({ queryKey: ["sessions"], queryFn: listSessions });
}

export function useSessionDetail(sessionId: string | undefined, refetchInterval?: number) {
  return useQuery({
    queryKey: ["sessions", sessionId],
    queryFn: () => getSession(sessionId as string),
    enabled: !!sessionId,
    refetchInterval,
  });
}

export function usePriceHistory(sessionId: string | undefined) {
  return useQuery({
    queryKey: ["sessions", sessionId, "price-history"],
    queryFn: () => getPriceHistory(sessionId as string),
    enabled: !!sessionId,
  });
}

export function useCreateSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: CreateSessionRequest) => {
      const session = await createSession(body);
      await startRun(session.id);
      return session;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["sessions"] });
    },
  });
}
