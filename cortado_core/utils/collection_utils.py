from collections import Counter


def count_unordered_sub_list_occurrences(list, sub_list):
    """ Counts the number of unordered occurrences of sub_list in list.

    Example:
    Assume we have the following inputs:

            list = [a,b,b,a,a,b]

            sub_list = [a,b]

    list contains sub_list 3 times. Note that [b,a] is also counted. 

    Parameters
    ----------
    list : List
    sub_list : List
    count: number
        number of unordered occurrences of sub_list in list.
    """

    # filter list s.t. it only contains the elements that are also contained in sub_list
    filtered = [x for x in list if x in sub_list]
    
    if not all(item in filtered for item in sub_list):
        return 0

    # create map with counts 
    counted = Counter(filtered)
    # the minimum count is the number of occurences
    return min(counted.values())


def count_ordererd_sub_list_occurrences(list, sub_list):
    """ Counts the number of ordered occurrences of sub_list in list. 

        Example:
        Assume we have the following inputs:

                list = [a,b,b,a,a,b]

                sub_list = [a,b]

        list contains sub_list 2 times. Note that [b,a] is not counted. 

        Parameters
        ----------
        list : List
        sub_list : List
        count: number
            number of ordered occurrences of sub_list in list. 
        """

    count = 0
    for i in range(len(list)-len(sub_list)+1):
        if sub_list == list[i:i+len(sub_list)]:
            count += 1
    return count
