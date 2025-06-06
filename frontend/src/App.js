import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [dashboardData, setDashboardData] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [ledgerEntries, setLedgerEntries] = useState([]);
  const [verifiedTransactions, setVerifiedTransactions] = useState([]);
  const [impactEntries, setImpactEntries] = useState([]);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (activeTab === 'dashboard') {
      fetchDashboardData();
    } else if (activeTab === 'ledger') {
      fetchLedgerEntries();
    } else if (activeTab === 'verified') {
      fetchVerifiedTransactions();
    } else if (activeTab === 'impact') {
      fetchImpactEntries();
    }
  }, [activeTab]);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/dashboard-summary`);
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };

  const fetchLedgerEntries = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/ledger-entries`);
      setLedgerEntries(response.data.ledger_entries);
    } catch (error) {
      console.error('Error fetching ledger entries:', error);
    }
  };

  const fetchVerifiedTransactions = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/verified-transactions`);
      setVerifiedTransactions(response.data.verified_transactions);
    } catch (error) {
      console.error('Error fetching verified transactions:', error);
    }
  };

  const fetchImpactEntries = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/impact-entries`);
      setImpactEntries(response.data.impact_entries);
    } catch (error) {
      console.error('Error fetching impact entries:', error);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setLoading(true);
    setUploadStatus('Processing invoice...');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/upload-invoice`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setUploadStatus('Invoice processed successfully!');
      setTimeout(() => {
        setUploadStatus('');
        if (activeTab === 'dashboard') {
          fetchDashboardData();
        }
      }, 2000);
    } catch (error) {
      setUploadStatus('Error processing invoice. Please try again.');
      console.error('Upload error:', error);
    } finally {
      setLoading(false);
      event.target.value = '';
    }
  };

  const handleImpactSubmit = async (impactData) => {
    try {
      await axios.post(`${API_BASE_URL}/api/impact-entry`, impactData);
      alert('Impact data saved successfully!');
      fetchImpactEntries();
    } catch (error) {
      alert('Error saving impact data');
      console.error('Impact submit error:', error);
    }
  };

  const TabButton = ({ id, label, active, onClick }) => (
    <button
      className={`px-6 py-3 rounded-lg font-medium transition-all duration-200 ${
        active
          ? 'bg-blue-600 text-white shadow-lg'
          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
      }`}
      onClick={onClick}
    >
      {label}
    </button>
  );

  const Dashboard = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-sm p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">Upload Invoice</h2>
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
          <input
            type="file"
            accept=".pdf,.jpg,.jpeg,.png"
            onChange={handleFileUpload}
            className="hidden"
            id="file-upload"
            disabled={loading}
          />
          <label htmlFor="file-upload" className="cursor-pointer">
            <div className="mx-auto w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <p className="text-lg font-medium text-gray-700 mb-2">
              {loading ? 'Processing...' : 'Drop invoice here or click to upload'}
            </p>
            <p className="text-sm text-gray-500">PDF, JPEG, PNG files up to 10MB</p>
          </label>
        </div>
        {uploadStatus && (
          <div className={`mt-4 p-4 rounded-lg ${
            uploadStatus.includes('Error') ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
          }`}>
            {uploadStatus}
          </div>
        )}
      </div>

      {dashboardData && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-sm font-medium text-gray-500 mb-2">Total Invoices</h3>
              <p className="text-3xl font-bold text-gray-900">{dashboardData.summary.total_invoices}</p>
            </div>
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-sm font-medium text-gray-500 mb-2">Total Amount</h3>
              <p className="text-3xl font-bold text-gray-900">${dashboardData.summary.total_amount.toFixed(2)}</p>
            </div>
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-sm font-medium text-gray-500 mb-2">CO₂ Emissions</h3>
              <p className="text-3xl font-bold text-gray-900">{dashboardData.summary.total_co2_emissions.toFixed(2)} tons</p>
            </div>
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-sm font-medium text-gray-500 mb-2">Avg Labor Score</h3>
              <p className="text-3xl font-bold text-gray-900">{dashboardData.summary.avg_labor_score}/10</p>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">Recent Transactions</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-medium text-gray-600">Date</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-600">Supplier</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-600">Amount</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-600">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {dashboardData.recent_invoices.map((invoice, index) => (
                    <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4">{invoice.data?.date || 'N/A'}</td>
                      <td className="py-3 px-4">{invoice.data?.supplier || 'N/A'}</td>
                      <td className="py-3 px-4">${invoice.data?.amount?.toFixed(2) || '0.00'}</td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">
                          Verified
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );

  const FinancialLedger = () => (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Financial Ledger</h2>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-3 px-4 font-medium text-gray-600">Date</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600">Supplier</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600">Account</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600">Debit</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600">Credit</th>
            </tr>
          </thead>
          <tbody>
            {ledgerEntries.map((entry) => (
              <tr key={entry.id} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-3 px-4">{entry.date}</td>
                <td className="py-3 px-4">{entry.supplier}</td>
                <td className="py-3 px-4">{entry.account}</td>
                <td className="py-3 px-4 text-green-600">
                  {entry.type === 'debit' ? `$${entry.amount.toFixed(2)}` : '-'}
                </td>
                <td className="py-3 px-4 text-red-600">
                  {entry.type === 'credit' ? `$${entry.amount.toFixed(2)}` : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const VerifiedTransactions = () => (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Verified Transactions (Immutable)</h2>
      <div className="space-y-4">
        {verifiedTransactions.map((transaction) => (
          <div key={transaction.id} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">Transaction ID</p>
                <p className="font-mono text-sm break-all">{transaction.id}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Supplier</p>
                <p className="font-medium">{transaction.supplier}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Amount</p>
                <p className="font-medium">${transaction.amount?.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Timestamp</p>
                <p className="font-medium">{new Date(transaction.timestamp).toLocaleString()}</p>
              </div>
              <div className="md:col-span-2">
                <p className="text-sm text-gray-600">Hash (Immutable Proof)</p>
                <p className="font-mono text-xs break-all bg-gray-100 p-2 rounded">{transaction.hash}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const ImpactLedger = () => {
    const [newImpact, setNewImpact] = useState({
      invoice_id: '',
      water_usage: 0,
      co2_emissions: 0,
      labor_score: 5,
      recycling_rate: 0
    });

    return (
      <div className="space-y-6">
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">Add Impact Data</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Invoice ID</label>
              <input
                type="text"
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter invoice ID"
                value={newImpact.invoice_id}
                onChange={(e) => setNewImpact({...newImpact, invoice_id: e.target.value})}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Water Usage (liters)</label>
              <input
                type="number"
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                value={newImpact.water_usage}
                onChange={(e) => setNewImpact({...newImpact, water_usage: parseFloat(e.target.value) || 0})}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">CO₂ Emissions (tons)</label>
              <input
                type="number"
                step="0.01"
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                value={newImpact.co2_emissions}
                onChange={(e) => setNewImpact({...newImpact, co2_emissions: parseFloat(e.target.value) || 0})}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Labor Score (1-10)</label>
              <input
                type="number"
                min="1"
                max="10"
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                value={newImpact.labor_score}
                onChange={(e) => setNewImpact({...newImpact, labor_score: parseInt(e.target.value) || 5})}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Recycling Rate (%)</label>
              <input
                type="number"
                min="0"
                max="100"
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                value={newImpact.recycling_rate}
                onChange={(e) => setNewImpact({...newImpact, recycling_rate: parseFloat(e.target.value) || 0})}
              />
            </div>
            <div className="flex items-end">
              <button
                onClick={() => handleImpactSubmit(newImpact)}
                className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Save Impact Data
              </button>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Impact Entries</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Supplier</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Amount</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Water (L)</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">CO₂ (tons)</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Labor Score</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Recycling %</th>
                </tr>
              </thead>
              <tbody>
                {impactEntries.map((entry) => (
                  <tr key={entry.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4">{entry.supplier}</td>
                    <td className="py-3 px-4">${entry.amount?.toFixed(2)}</td>
                    <td className="py-3 px-4">{entry.water_usage}</td>
                    <td className="py-3 px-4">{entry.co2_emissions}</td>
                    <td className="py-3 px-4">{entry.labor_score}/10</td>
                    <td className="py-3 px-4">{entry.recycling_rate}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto p-6">
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">QuadLedger</h1>
          <p className="text-gray-600">Intelligent Quad-Entry Bookkeeping with AI-Powered Invoice Processing</p>
        </header>

        <nav className="mb-8">
          <div className="flex space-x-4 overflow-x-auto">
            <TabButton
              id="dashboard"
              label="Dashboard"
              active={activeTab === 'dashboard'}
              onClick={() => setActiveTab('dashboard')}
            />
            <TabButton
              id="ledger"
              label="Financial Ledger"
              active={activeTab === 'ledger'}
              onClick={() => setActiveTab('ledger')}
            />
            <TabButton
              id="verified"
              label="Verified Transactions"
              active={activeTab === 'verified'}
              onClick={() => setActiveTab('verified')}
            />
            <TabButton
              id="impact"
              label="Impact Ledger"
              active={activeTab === 'impact'}
              onClick={() => setActiveTab('impact')}
            />
          </div>
        </nav>

        <main>
          {activeTab === 'dashboard' && <Dashboard />}
          {activeTab === 'ledger' && <FinancialLedger />}
          {activeTab === 'verified' && <VerifiedTransactions />}
          {activeTab === 'impact' && <ImpactLedger />}
        </main>
      </div>
    </div>
  );
}

export default App;