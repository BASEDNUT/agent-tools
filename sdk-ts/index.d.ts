export type JsonPrimitive = string | number | boolean | null;
export type Json = JsonPrimitive | Json[] | { [key: string]: Json };
export interface RootstockClientOptions {
  command?: string;
  prefix?: string[];
  timeoutMs?: number;
  env?: Record<string, string | undefined>;
}
/** Local subprocess client; all validation/execution lives in Python Toolchain. */
export declare class RootstockClient {
  constructor(options?: RootstockClientOptions);
  call(name: string, args?: Record<string, Json>): Json;
  capabilities(): Json;
  skills(): Json;
  networks(): Json;
}
