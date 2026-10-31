export { ApiError, errorMessage, jsonBody, requestJson } from "./request";
export type { ApiErrorBody } from "./request";

export interface Page<T> {
  page: number;
  size: number;
  total: number;
  items: T[];
}
