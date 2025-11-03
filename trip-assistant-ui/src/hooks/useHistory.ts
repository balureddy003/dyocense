import history from "../data/historyTrips.json";

export interface PastTrip {
  id: number;
  title: string;
  dates: string;
}

export const useHistory = (): PastTrip[] => history;
