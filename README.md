# cccw  
  
Cloud Coin Console Wallet  
  
Examples:  
  
Show inventory  
$ cccw.py bank  
Bank Inventory  
        1s:          1, coins: 1  
        5s:          0, coins: 0  
       25s:          0, coins: 0  
      100s:          0, coins: 0  
      250s:     475750, coins: 1903  
     Total:     475751, coins: 1904  


Import coins from dir and one file  
$ cccw.py import --path /home/user/coinsdir /home/user/coin.stack  
  
Export coins  
$ cccw.py export --coins 250:3 100:4  
  
Fix fracked  
$ cccw.py fixfracked  
  
Validate coins in the Bank  
$ cccw.py verify  
  
