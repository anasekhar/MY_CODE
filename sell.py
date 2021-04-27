class Solution(object):
    def maxProfit(self, prices, fee):
        """
        :type prices: List[int]
        :type fee: int
        :rtype: int
        """
        cash, hold = 0, -prices[0]
        for i in range(1, len(prices)):
            print("cash hold",cash,hold)
            cash = max(cash, hold + prices[i] - fee)
            hold = max(hold, cash - prices[i])
        return cash


obj = Solution()
print(obj.maxProfit([1,3,2,8,4,9],2))
