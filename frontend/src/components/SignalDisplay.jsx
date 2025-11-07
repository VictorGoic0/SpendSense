import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Progress } from './ui/progress';

/**
 * SignalDisplay Component
 * Displays signal information for different signal types
 * 
 * @param {Object} props
 * @param {Object} props.signals - Signals object with subscriptions, savings, credit, income
 * @param {string} props.signalType - Type of signal to display (subscriptions/savings/credit/income)
 * @param {string} props.title - Optional title for the card
 */
export default function SignalDisplay({ signals, signalType, title }) {
  if (!signals || !signalType) {
    return null;
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  const formatPercentage = (value) => {
    if (value === null || value === undefined) return 'N/A';
    return `${(value * 100).toFixed(1)}%`;
  };

  // Subscriptions view
  if (signalType === 'subscriptions') {
    const subscriptionData = signals.subscriptions;
    if (!subscriptionData) return null;

    const recurringMerchants = subscriptionData.recurring_merchants || [];
    const monthlySpend = subscriptionData.monthly_spend || 0;
    const spendShare = subscriptionData.spend_share || 0;
    const spendSharePercent = spendShare * 100;

    return (
      <Card>
        <CardHeader>
          <CardTitle>{title || 'Subscription Signals'}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-500">Recurring Merchants</label>
            <p className="text-2xl font-semibold text-gray-900 mt-1">
              {recurringMerchants.length}
            </p>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-500">Monthly Recurring Spend</label>
            <p className="text-2xl font-semibold text-gray-900 mt-1">
              {formatCurrency(monthlySpend)}
            </p>
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-medium text-gray-500">Subscription Spend Share</label>
              <span className="text-sm font-semibold text-gray-900">
                {formatPercentage(spendShare)}
              </span>
            </div>
            <Progress value={spendSharePercent} className="h-3" />
          </div>

          {recurringMerchants.length > 0 && (
            <div>
              <label className="text-sm font-medium text-gray-500 mb-2 block">
                Recurring Merchants
              </label>
              <ul className="space-y-1">
                {recurringMerchants.map((merchant, index) => (
                  <li key={index} className="text-sm text-gray-700 flex items-center">
                    <span className="w-2 h-2 rounded-full bg-blue-500 mr-2"></span>
                    {merchant}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  // Placeholder for other signal types (will be implemented in next tasks)
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title || `${signalType} Signals`}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-gray-500">Coming soon</p>
      </CardContent>
    </Card>
  );
}

