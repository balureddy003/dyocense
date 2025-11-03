import history from "../data/historyTrips.json";

export interface PastTrip {
  id: number;
  title: string;
  dates: string;
  meta?: {
    duration?: string;
    cities?: string;
  };
}

export const useHistory = (): PastTrip[] => history as PastTrip[];
