import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Progress } from './ui/progress';
import { Badge } from './ui/badge';

/**
 * SignalDisplay Component
 * Displays signal information for different signal types
 * 
 * @param {Object} props
 * @param {Object} props.signals - Signals object with subscriptions, savings, credit, income
 * @param {string} props.signalType - Type of signal to display (subscriptions/savings/credit/income)
 * @param {string} props.title - Optional title for the card
 * @param {Object} props.profile - Optional profile data for additional flags (credit flags)
 */
export default function SignalDisplay({ signals, signalType, title, profile }) {
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

  const getUtilizationColor = (utilization) => {
    if (utilization < 0.30) return 'bg-green-500';
    if (utilization < 0.50) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getEmergencyFundColor = (months) => {
    if (months < 1) return 'bg-red-500';
    if (months < 3) return 'bg-yellow-500';
    return 'bg-green-500';
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

  // Savings view
  if (signalType === 'savings') {
    const savingsData = signals.savings;
    if (!savingsData) return null;

    const netInflow = savingsData.net_inflow || 0;
    const growthRate = savingsData.growth_rate || 0;
    const emergencyFundMonths = savingsData.emergency_fund_months || 0;
    // Target: 3-6 months, so show progress up to 6 months
    const emergencyFundPercent = Math.min((emergencyFundMonths / 6) * 100, 100);

    return (
      <Card>
        <CardHeader>
          <CardTitle>{title || 'Savings Signals'}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-500">Net Savings Inflow</label>
            <p className="text-2xl font-semibold text-gray-900 mt-1">
              {formatCurrency(netInflow)}
            </p>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-500">Savings Growth Rate</label>
            <p className="text-2xl font-semibold text-gray-900 mt-1">
              {formatPercentage(growthRate)}
            </p>
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-medium text-gray-500">Emergency Fund Coverage</label>
              <span className="text-sm font-semibold text-gray-900">
                {emergencyFundMonths.toFixed(1)} months
              </span>
            </div>
            <div className="relative">
              <Progress 
                value={emergencyFundPercent} 
                className="h-3"
              />
              <div 
                className={`absolute top-0 left-0 h-3 rounded-full ${getEmergencyFundColor(emergencyFundMonths)}`}
                style={{ width: `${emergencyFundPercent}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">Target: 3-6 months</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Credit view
  if (signalType === 'credit') {
    const creditData = signals.credit;
    if (!creditData) return null;

    const cards = creditData.cards || [];
    // Get avg/max utilization from profile if available, otherwise calculate from cards
    const features30d = profile?.features?.['30d'];
    const avgUtilization = features30d?.avg_utilization || 
      (cards.length > 0 ? cards.reduce((sum, card) => sum + card.utilization, 0) / cards.length : 0);
    const maxUtilization = features30d?.max_utilization ||
      (cards.length > 0 ? Math.max(...cards.map(card => card.utilization)) : 0);
    const flags = {
      minimumPaymentOnly: features30d?.minimum_payment_only_flag || false,
      interestCharges: features30d?.interest_charges_present || false,
      overdue: features30d?.any_overdue || false,
    };

    return (
      <Card>
        <CardHeader>
          <CardTitle>{title || 'Credit Signals'}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-medium text-gray-500">Average Utilization</label>
              <span className="text-sm font-semibold text-gray-900">
                {formatPercentage(avgUtilization)}
              </span>
            </div>
            <Progress 
              value={avgUtilization * 100} 
              className={`h-3 ${getUtilizationColor(avgUtilization)}`}
            />
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-medium text-gray-500">Max Utilization</label>
              <span className="text-sm font-semibold text-gray-900">
                {formatPercentage(maxUtilization)}
              </span>
            </div>
            <Progress 
              value={maxUtilization * 100} 
              className={`h-3 ${getUtilizationColor(maxUtilization)}`}
            />
          </div>

          {cards.length > 0 && (
            <div>
              <label className="text-sm font-medium text-gray-500 mb-2 block">
                Credit Cards
              </label>
              <div className="space-y-3">
                {cards.map((card, index) => (
                  <div key={index} className="border rounded-lg p-3">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-gray-900">
                        •••• {card.last_four}
                      </span>
                      <span className="text-sm font-semibold text-gray-900">
                        {formatPercentage(card.utilization)}
                      </span>
                    </div>
                    <Progress 
                      value={card.utilization * 100} 
                      className={`h-2 ${getUtilizationColor(card.utilization)}`}
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>Balance: {formatCurrency(card.balance)}</span>
                      <span>Limit: {formatCurrency(card.limit)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {(flags.minimumPaymentOnly || flags.interestCharges || flags.overdue) && (
            <div>
              <label className="text-sm font-medium text-gray-500 mb-2 block">
                Warning Flags
              </label>
              <div className="flex flex-wrap gap-2">
                {flags.minimumPaymentOnly && (
                  <Badge variant="outline" className="bg-yellow-100 text-yellow-800 border-yellow-200">
                    Minimum Payment Only
                  </Badge>
                )}
                {flags.interestCharges && (
                  <Badge variant="outline" className="bg-orange-100 text-orange-800 border-orange-200">
                    Interest Charges
                  </Badge>
                )}
                {flags.overdue && (
                  <Badge variant="outline" className="bg-red-100 text-red-800 border-red-200">
                    Overdue
                  </Badge>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  // Income view
  if (signalType === 'income') {
    const incomeData = signals.income;
    if (!incomeData) return null;

    const payrollDetected = incomeData.payroll_detected || false;
    const avgMonthly = incomeData.avg_monthly || 0;
    const medianPayGap = incomeData.median_pay_gap_days;
    const incomeVariability = incomeData.income_variability;
    const cashFlowBuffer = incomeData.cash_flow_buffer_months || 0;
    const frequency = incomeData.frequency || 'unknown';

    const showBufferWarning = cashFlowBuffer < 1;
    const showVariabilityWarning = incomeVariability && incomeVariability > 0.30;

    return (
      <Card>
        <CardHeader>
          <CardTitle>{title || 'Income Signals'}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-500">Payroll Detected</label>
            <div className="mt-1">
              <Badge
                variant="outline"
                className={
                  payrollDetected
                    ? 'bg-green-100 text-green-800 border-green-200'
                    : 'bg-gray-100 text-gray-800 border-gray-200'
                }
              >
                {payrollDetected ? 'Yes' : 'No'}
              </Badge>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-500">Average Monthly Income</label>
            <p className="text-2xl font-semibold text-gray-900 mt-1">
              {formatCurrency(avgMonthly)}
            </p>
          </div>

          {medianPayGap !== null && medianPayGap !== undefined && (
            <div>
              <label className="text-sm font-medium text-gray-500">Median Pay Gap</label>
              <p className="text-base text-gray-900 mt-1">{medianPayGap} days</p>
            </div>
          )}

          {incomeVariability !== null && incomeVariability !== undefined && (
            <div>
              <label className="text-sm font-medium text-gray-500">Income Variability</label>
              <div className="flex items-center gap-2 mt-1">
                <p className="text-base font-semibold text-gray-900">
                  {formatPercentage(incomeVariability)}
                </p>
                {showVariabilityWarning && (
                  <Badge variant="outline" className="bg-yellow-100 text-yellow-800 border-yellow-200">
                    High Variability
                  </Badge>
                )}
              </div>
            </div>
          )}

          <div>
            <label className="text-sm font-medium text-gray-500">Cash Flow Buffer</label>
            <div className="flex items-center gap-2 mt-1">
              <p className="text-base font-semibold text-gray-900">
                {cashFlowBuffer.toFixed(1)} months
              </p>
              {showBufferWarning && (
                <Badge variant="outline" className="bg-red-100 text-red-800 border-red-200">
                  Low Buffer
                </Badge>
              )}
            </div>
          </div>

          {frequency !== 'unknown' && (
            <div>
              <label className="text-sm font-medium text-gray-500">Payment Frequency</label>
              <p className="text-base text-gray-900 mt-1 capitalize">{frequency}</p>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  // Unknown signal type
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title || `${signalType} Signals`}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-gray-500">Unknown signal type</p>
      </CardContent>
    </Card>
  );
}

