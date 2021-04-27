class Solution(object):
    def removePalindromeSub(self, s):
        """
        :type s: str
        :rtype: int
        """
        print("Given string :", s)
        str_len = len(s)
        if str_len  == 1 :
            return 1
        if str_len == 0 :
            return 0
        count = 1
        pal_count=0
        while(count <= str_len/2) :
            print(count)
            if self.palindrome(s[:str_len-count]):
                pal_count=pal_count+1
            if self.palindrome(s[count:]):
                if s[count:] != s[:str_len-count]:
                  pal_count = pal_count+1
            count = count + 1
        else:
            return pal_count

    def palindrome(self,pal_str):
        print("comp str",pal_str)
        if str(pal_str) == str(pal_str[::-1]):
            return 1
        else:
            return 0

obj = Solution()
output = obj.removePalindromeSub("abb")
print("numbe of pal",output)
