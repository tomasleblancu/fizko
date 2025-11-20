// ChatKit tool type definitions for Fizko

export interface SwitchThemeTool {
  name: "switch_theme";
  params: {
    theme: "light" | "dark";
  };
}

export interface RefreshCompanyTool {
  name: "refresh_company";
  params: {
    company_id: string;
  };
}

export type ChatKitTool = SwitchThemeTool | RefreshCompanyTool;
