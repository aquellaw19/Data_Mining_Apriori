import csv
import math
import time
import glob
from itertools import combinations

def get_file_names():
    # get the name of all files ending with .csv
    files = glob.glob(('*.csv*'))
    return files

def load_transactions(file_name):
    DB =[]
    with open(file_name, mode = 'r', encoding='utf-8-sig') as csvfile:
        file_reader = csv.reader(csvfile)
        for row in file_reader:
            DB.append(row)
    return DB

def transaction_count(DB):
    item_set = {}
    for t in DB:
        #casting transcaction as a set prevents double counting within a transaction
        for item in set(t):
            item_set[item] = item_set.get(item, 0)+1
    return item_set

def generate_candidate_set(k, prev_fk):
    candidates = set()
    F_prev = set(prev_fk.keys())
    H = list(F_prev)

    for i in range(len(H)):
        for j in range(i+1,len(H)):
            set_a = H[i]
            set_b = H[j]
             
            candidate_set = set_a.union(set_b)
            if len(candidate_set) == k:  

                #candidate itemset should be discarded if one of its
                # subsets is infrequent.
                keep_subset = True

                #If a subset of the combination set is not in the k-1
                #frequent set, exist loop
                for subset in combinations(candidate_set, k-1):
                    if frozenset(subset) not in F_prev:
                        keep_subset = False
                        break
                        
                if keep_subset:
                  candidates.add(candidate_set)    
    return candidates       

def count_support (candidates, DB):
    #Creates dictionary and initializes each candicate's value as 0.
    support = {candidate: 0 for candidate in candidates}
    for t in DB:
        for c in candidates:
            if c.issubset(set(t)):
                support[c] +=1
    return support

def apriori_gen(DB, minsup):

    #if minsup is not an int, multiply minsup by the num transactions and take the ceiling
    if not isinstance(minsup, int):
        minsup = math.ceil(len(DB) * minsup)
        
    #-------F1------
    item_counts = transaction_count(DB)
    #Contains all frequent items that are greater than or equal to the minimum support
    F_prev = {frozenset([item]): count for item, count in item_counts.items() if count >= minsup}
    
    #Stores all frequent items. eg. {1: {k-1 frequent_items: count}}
    Fk_all = {1:F_prev}
    k = 2

    #keep loop running where there are still frequent itemsets
    while F_prev: 

        #------Generate  condidates ck from F_k-1----------
        ck = generate_candidate_set(k,F_prev)

        #If no condidates were found, exist loop
        if not ck:
            break

        #---------Count support for condidates--------
        support = count_support(ck, DB)

        #------------------Filter by minsup and build Fk-----------
        #Contains all candidates whose support is greater than or equal to the minimum support
        Fk = {candidate:count for candidate, count in support.items() if count >= minsup}

        #If no fequent items were found from the k-1 itemset, exit loop
        if not Fk:
            break

        Fk_all[k] = Fk
        F_prev = Fk
        k += 1

    return Fk_all

def gen_hm_1(Hm):
    H = list(Hm)

    #if h is empty, return an empy set
    if not H:
        return set()
    
    m = len(H[0])
    Hm1 = set()

    for i in range(len(H)):
        for j in range(i+1,len(H)):
            rule_a = H[i]
            rule_b = H[j]
             
            candidate_set = rule_a.union(rule_b)
            if len(candidate_set) != m+1: 
                continue 

                #If a subset of the combination set is not in Hm
                # exist loop
            for subset in combinations(candidate_set, m):
                if frozenset(subset) not in Hm:
                    break
            else:               
                Hm1.add(candidate_set)    
    return Hm1       

def ap_gen_rules(fk, Hm, support_data, minconf, rules):
    if not Hm:
        return rules
    
    fk_size = len(fk)
    #size of one consequent
    rule_consqnt =len(next(iter(Hm)))
    
    #Tracks consequents that passed the confidence threshold
    Hm_keep = set()

    for h in Hm:
        #Full itemset - the consequent (antedecent)
        left_side = fk - h 

        #If antedecent is empty, skip
        if not left_side:
            continue
            
        sup_fk = support_data.get(fk, 0)
        sup_lhs = support_data.get(left_side, 0)

        if sup_fk == 0 or sup_lhs == 0:
            continue

        conf =  sup_fk / sup_lhs

        if conf >= minconf:
            #If the rule passes, record and keep the consequent for further expansion
            rules.append((left_side, h, conf))  
            print(f"{set(left_side)} -> {set(h)}  (conf={conf:.3f})")
            Hm_keep.add(h)

        #If itemset is large enough, expand the the consequent
        if fk_size>rule_consqnt + 1 and Hm_keep:
                next_Hm = gen_hm_1(Hm_keep)
                if next_Hm:
                    ap_gen_rules(fk, next_Hm, support_data, minconf, rules)
    return rules

def brute_candidates(items, k):
    # returns a set of frozensets, each size k
    return {frozenset(c) for c in combinations(items, k)}

def brute_force_gen(DB, minsup):
    # Convert minsup if it's fractional
    if not isinstance(minsup, int):
        minsup = math.ceil(len(DB) * minsup)

    items = get_item_universe(DB)     # all unique items
    Fk_all = {}
    k = 1

    while True:
        # Generate ALL possible k-itemsets
        ck = brute_candidates(items, k)
        # Count supports (reuse your function)
        support = count_support(ck, DB)
        # Filter by minsup
        Fk = {candidate: cnt for candidate, cnt in support.items() if cnt >= minsup}
        if not Fk:
            break
        Fk_all[k] = Fk
        k += 1
    return Fk_all

def get_item_universe(DB):
    items = set()
    for t in DB:
        items.update(set(t))
    return sorted(items)

def main():
    rules = []
    minconf = .2
    minsup = 9

    #Retreives all file names
    file_names = get_file_names()

    for file in file_names:
        print(f"=================Results for {file}=================")
        #Loads transactions into lists
        transactions_DB = load_transactions(file)

        #-------------------Apriori Algorithm-----------------------------
        ap_start_time = time.perf_counter()
        Fk_all = apriori_gen(transactions_DB, minsup) 
        ap_end_time = time.perf_counter()
        ap_total_time = ap_end_time - ap_start_time
        print(f"Frequent items using Apriori:\n {Fk_all} \n")
        print(f"Time Elapsed for Apriori: {ap_total_time:.4f} seconds\n")
        

        #Stores support data for all k-1 itemsets
        support_data = {}
        for level in Fk_all.values():
            support_data.update(level)

        # generate association rules
        for itemset_size, item_set in Fk_all.items():
            if itemset_size >= 2:
                for fk in item_set:
                    H1 = {frozenset([item]) for item in fk}
                    ap_gen_rules(fk, H1, support_data, minconf, rules)

        #--------------------Brute force Algorithm----------------------
        brute_start_time = time.perf_counter()
        Fk_brute = brute_force_gen(transactions_DB, minsup)
        brute_end_time = time.perf_counter()
        brute_total_time = brute_end_time - brute_start_time

        print("Brute force Itemsets and length\n")
        for k in sorted(Fk_brute):
            print(k, "itemsets:", len(Fk_brute[k]))
        print(f"Time Elapsed for Brute force: {brute_total_time:.4f} seconds\n")
        
if __name__ == "__main__":
    main()

