import axios from "axios";
import http from "./api";

export type SmsLogRow = {
  id: number;
  batchId: string;
  phoneMasked: string;
  templateCode: string;
  status: number;
  receipt?: string;
  errorMsg?: string;
  content?: string;
  createdAt: string;
};

export type SendSmsResult = {
  batchId: string;
};

export const sendSms = (
  templateCode: string,
  phones: string[],
  vars: Record<string, string> = {}
) => http.post("/sms/send", { templateCode, phones, vars }) as Promise<SendSmsResult>;

export const getSmsLog = (batchId?: string) =>
  http.get("/sms/log", { params: { batch_id: batchId } }) as Promise<SmsLogRow[]>;

export function isSmsBackendUnreachable(err: unknown): boolean {
  if (!axios.isAxiosError(err)) return false;
  return !err.response || err.response.status >= 500;
}

export function maskPhone(phone: string): string {
  if (typeof phone !== "string" || phone.length !== 11) return phone;
  return `${phone.slice(0, 3)}****${phone.slice(-4)}`;
}
