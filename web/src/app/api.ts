export interface Model {
  id: string;
  name: string;
  architecture: string;
  param_count: number;
  context_length: number;
  license: string;
  source: string;
}

export interface Dataset {
  id: string;
  name: string;
  source: string;
  license: string;
  overlap_rate?: number;
  pii_risk?: number;
}

export interface Experiment {
  id: string;
  name: string;
  model_version_id: string;
  dataset_version_id: string;
  strategy_id: string;
  seed: number;
  status: string; // REAL, DEMO, ESTIMATE, FAILED, etc.
  created_at: string;
  avg_accuracy?: number;
  forgetting_score?: number;
}

export interface Job {
  id: string;
  job_type: string;
  status: string; // queued, running, succeeded, failed, cancelled
  progress: number;
  created_at: string;
}

const API_BASE = "http://localhost:8000/api/v1";

async function fetchFromApi<T>(path: string, fallbackData: T): Promise<{ data: T; status: "REAL" | "DEMO" }> {
  try {
    const token = localStorage.getItem("token") || "";
    const headers: RequestInit = {
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      }
    };
    const res = await fetch(`${API_BASE}${path}`, headers);
    if (!res.ok) throw new Error("API call failed");
    const json = await res.json();
    return { data: json as T, status: "REAL" };
  } catch (err) {
    console.warn(`API path ${path} unreachable. Falling back to deterministic demo adapter.`, err);
    return { data: fallbackData, status: "DEMO" };
  }
}

// --- DETERMINISTIC DEMO FALLBACKS ---
export const DEMO_MODELS: Model[] = [
  { id: "tinyllama-1.1b", name: "TinyLlama 1.1B", architecture: "LlamaForCausalLM", param_count: 1100000000, context_length: 2048, license: "Apache-2.0", source: "HuggingFace" },
  { id: "phi-2", name: "Phi-2 2.7B", architecture: "MixformerSequential", param_count: 2700000000, context_length: 2048, license: "MIT", source: "HuggingFace" }
];

export const DEMO_DATASETS: Dataset[] = [
  { id: "dataset_triviaqa", name: "TriviaQA Bench", source: "HuggingFace trivia_qa", license: "Apache-2.0", overlap_rate: 0.012, pii_risk: 0.0 },
  { id: "dataset_gsm8k", name: "GSM8K Math Bench", source: "HuggingFace gsm8k", license: "MIT", overlap_rate: 0.005, pii_risk: 0.0 }
];

export const DEMO_EXPERIMENTS: Experiment[] = [
  { id: "exp-001", name: "TinyLlama fine-tune EWC", model_version_id: "tinyllama-1.1b-v1", dataset_version_id: "dataset_triviaqa-v1", strategy_id: "ewc", seed: 42, status: "REAL", created_at: "2026-07-18T01:00:00Z", avg_accuracy: 0.735, forgetting_score: 0.082 },
  { id: "exp-002", name: "TinyLlama sequential FT", model_version_id: "tinyllama-1.1b-v1", dataset_version_id: "dataset_triviaqa-v1", strategy_id: "finetune_baseline", seed: 42, status: "REAL", created_at: "2026-07-18T01:15:00Z", avg_accuracy: 0.510, forgetting_score: 0.235 },
  { id: "exp-003", name: "Phi-2 Replay strategy", model_version_id: "phi-2-v1", dataset_version_id: "dataset_gsm8k-v1", strategy_id: "experience_replay", seed: 42, status: "DEMO", created_at: "2026-07-18T02:00:00Z", avg_accuracy: 0.812, forgetting_score: 0.045 }
];

export const DEMO_JOBS: Job[] = [
  { id: "job-ft-abc1", job_type: "fine-tune", status: "succeeded", progress: 100.0, created_at: "2026-07-18T01:00:00Z" },
  { id: "job-ev-abc2", job_type: "evaluate", status: "succeeded", progress: 100.0, created_at: "2026-07-18T01:05:00Z" },
  { id: "job-ft-active", job_type: "fine-tune", status: "running", progress: 65.5, created_at: "2026-07-18T05:00:00Z" }
];

// --- API ACTIONS ---
export async function getModels(workspaceId: string = "workspace_default") {
  return fetchFromApi<Model[]>(`/${workspaceId}/models`, DEMO_MODELS);
}

export async function registerModel(model: Model, workspaceId: string = "workspace_default") {
  try {
    const token = localStorage.getItem("token") || "";
    const res = await fetch(`${API_BASE}/${workspaceId}/models`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify(model)
    });
    if (!res.ok) throw new Error("API call failed");
    const json = await res.json();
    return { data: json as Model, status: "REAL" as const };
  } catch (err) {
    console.warn(`API call to register model failed. Simulating in-memory registration.`, err);
    DEMO_MODELS.push(model);
    return { data: model, status: "DEMO" as const };
  }
}

export async function getDatasets(workspaceId: string = "workspace_default") {
  return fetchFromApi<Dataset[]>(`/${workspaceId}/datasets`, DEMO_DATASETS);
}

export async function getExperiments(workspaceId: string = "workspace_default") {
  return fetchFromApi<Experiment[]>(`/${workspaceId}/experiments`, DEMO_EXPERIMENTS);
}

export async function getJobs(workspaceId: string = "workspace_default") {
  try {
    const res = await fetch(`${API_BASE}/${workspaceId}/jobs/active`);
    if (!res.ok) throw new Error();
    const json = await res.json();
    return { data: json as Job[], status: "REAL" as const };
  } catch {
    return { data: DEMO_JOBS, status: "DEMO" as const };
  }
}


export async function login(email: string, password: string) {
  const formData = new FormData();
  formData.append("username", email);
  formData.append("password", password);
  
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    body: formData,
  });
  
  if (!res.ok) {
    const errorDetail = await res.json().catch(() => ({}));
    throw { response: { data: errorDetail } };
  }
  
  const data = await res.json();
  return { data };
}

export async function signup(email: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/signup?email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`, {
    method: "POST",
  });
  
  if (!res.ok) {
    const errorDetail = await res.json().catch(() => ({}));
    throw { response: { data: errorDetail } };
  }
  
  const data = await res.json();
  return { data };
}

