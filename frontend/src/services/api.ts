import type { 
  User, ExecutiveOverview, FinanceMetric, OperationsMetric, 
  CustomerMetric, BusinessRecommendation, ModelMetadata, DriftReport 
} from '../types';

const API_BASE_URL = 'http://localhost:8000/api/v1';

function getHeaders(): HeadersInit {
  const token = localStorage.getItem('access_token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  };
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage = `API Error ${response.status}`;
    try {
      const errorJson = JSON.parse(errorText);
      errorMessage = errorJson.detail || errorMessage;
    } catch {
      // Use raw text if not JSON
      if (errorText) errorMessage = errorText;
    }
    throw new Error(errorMessage);
  }
  return response.json() as Promise<T>;
}

export const api = {
  auth: {
    login: async (username: string, password: string): Promise<any> => {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: formData.toString()
      });
      return handleResponse<any>(response);
    },
    
    register: async (user: User & { password: string }): Promise<User> => {

      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(user)
      });
      return handleResponse<User>(response);
    },
    
    me: async (): Promise<User> => {
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        method: 'GET',
        headers: getHeaders()
      });
      return handleResponse<User>(response);
    }
  },

  analytics: {
    getOverview: async (): Promise<ExecutiveOverview> => {
      const response = await fetch(`${API_BASE_URL}/analytics/overview`, {
        method: 'GET',
        headers: getHeaders()
      });
      return handleResponse<ExecutiveOverview>(response);
    },
    
    getFinance: async (): Promise<FinanceMetric[]> => {
      const response = await fetch(`${API_BASE_URL}/analytics/finance`, {
        method: 'GET',
        headers: getHeaders()
      });
      return handleResponse<FinanceMetric[]>(response);
    },
    
    getOperations: async (): Promise<OperationsMetric[]> => {
      const response = await fetch(`${API_BASE_URL}/analytics/operations`, {
        method: 'GET',
        headers: getHeaders()
      });
      return handleResponse<OperationsMetric[]>(response);
    },
    
    getCustomers: async (): Promise<CustomerMetric[]> => {
      const response = await fetch(`${API_BASE_URL}/analytics/customers`, {
        method: 'GET',
        headers: getHeaders()
      });
      return handleResponse<CustomerMetric[]>(response);
    }
  },

  prediction: {
    predictRevenue: async (payload: any[]): Promise<any> => {
      const response = await fetch(`${API_BASE_URL}/prediction/revenue`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(payload)
      });
      return handleResponse<any>(response);
    },
    
    predictChurn: async (payload: any[]): Promise<any> => {
      const response = await fetch(`${API_BASE_URL}/prediction/churn`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(payload)
      });
      return handleResponse<any>(response);
    },
    
    predictRisk: async (payload: any[], riskType = 'customer'): Promise<any> => {
      const response = await fetch(`${API_BASE_URL}/prediction/risk?risk_type=${riskType}`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(payload)
      });
      return handleResponse<any>(response);
    },
    
    predictDemand: async (payload: any[]): Promise<any> => {
      const response = await fetch(`${API_BASE_URL}/prediction/demand`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(payload)
      });
      return handleResponse<any>(response);
    }
  },

  recommendations: {
    get: async (): Promise<BusinessRecommendation[]> => {
      const response = await fetch(`${API_BASE_URL}/recommendation`, {
        method: 'GET',
        headers: getHeaders()
      });
      return handleResponse<BusinessRecommendation[]>(response);
    },
    
    regenerate: async (): Promise<any> => {
      const response = await fetch(`${API_BASE_URL}/recommendation/generate`, {
        method: 'POST',
        headers: getHeaders()
      });
      return handleResponse<any>(response);
    }
  },

  explainability: {
    getGlobal: async (modelName: string): Promise<any> => {
      const response = await fetch(`${API_BASE_URL}/explainability/global?model_name=${modelName}`, {
        method: 'GET',
        headers: getHeaders()
      });
      return handleResponse<any>(response);
    },
    
    getLocal: async (payload: any, modelName: string): Promise<any> => {
      const response = await fetch(`${API_BASE_URL}/explainability/local?model_name=${modelName}`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(payload)
      });
      return handleResponse<any>(response);
    }
  },

  admin: {
    getModels: async (): Promise<ModelMetadata[]> => {
      const response = await fetch(`${API_BASE_URL}/admin/models`, {
        method: 'GET',
        headers: getHeaders()
      });
      return handleResponse<ModelMetadata[]>(response);
    },
    
    checkDrift: async (payload: any[], datasetName: string): Promise<DriftReport> => {
      const response = await fetch(`${API_BASE_URL}/admin/check-drift?dataset_name=${datasetName}`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(payload)
      });
      return handleResponse<DriftReport>(response);
    },
    
    getDriftLogs: async (): Promise<any[]> => {
      const response = await fetch(`${API_BASE_URL}/admin/drift-logs`, {
        method: 'GET',
        headers: getHeaders()
      });
      return handleResponse<any[]>(response);
    }
  }
};
