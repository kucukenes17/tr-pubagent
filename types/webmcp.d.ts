export {};

declare global {
  interface ModelContextTool {
    name: string;
    title?: string;
    description: string;
    inputSchema: Record<string, unknown>;
    annotations?: { readOnlyHint?: boolean; untrustedContentHint?: boolean };
    execute(input: unknown): Promise<unknown> | Record<string, unknown>;
  }

  interface ModelContext {
    registerTool(tool: ModelContextTool, options?: { signal?: AbortSignal }): void | Promise<void>;
  }

  interface Document {
    readonly modelContext?: ModelContext;
  }
}
