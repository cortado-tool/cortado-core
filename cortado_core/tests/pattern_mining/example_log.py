from pm4py.util.xes_constants import DEFAULT_NAME_KEY, DEFAULT_START_TIMESTAMP_KEY, DEFAULT_TIMESTAMP_KEY, \
    DEFAULT_TRANSITION_KEY
    
from pm4py.objects.log.obj import EventLog, Event, Trace
from datetime import datetime, timedelta




def create_example_log_1(): 
    """
        →(H, ∧(G, →(B, C)), K)
        →(H, ∧(G, →(B, C))) ^2
        →(A, B) ^2 
        →(H, B, C) ^ 2
        →(A, B, A, B)
        →(A, A, B)
        →(A, B, C)
        →(A, ∧(B, C))
        →(A, ∧(B, C, D))
        ∧(I, →(A, ∧(B, C)))
    """
    
    l = EventLog()

    #
    # *---A---* 
    #           *--B--*    

    e1 = Event()
    e2 = Event()
    e1[DEFAULT_NAME_KEY] = 'A'
    e1[DEFAULT_START_TIMESTAMP_KEY] = datetime.now()
    e1[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=1)

    e2[DEFAULT_NAME_KEY] = 'B'
    e2[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2)
    e2[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2.5)

    t = Trace()
    t.append(e1)
    t.append(e2)
    l.append(t)

    #
    # *---A---* 
    #           *--B--*   
    #                    *---A---* 
    #                               *---B---*


    e1 = Event()
    e2 = Event()
    e3 = Event()
    e4 = Event()
    e1[DEFAULT_NAME_KEY] = 'A'
    e1[DEFAULT_START_TIMESTAMP_KEY] = datetime.now()
    e1[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=1)

    e2[DEFAULT_NAME_KEY] = 'B'
    e2[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2)
    e2[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2.5)

    e3[DEFAULT_NAME_KEY] = 'A'
    e3[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours = 3)
    e3[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours= 3.5)

    e4[DEFAULT_NAME_KEY] = 'B'
    e4[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours= 4)
    e4[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=4.5)


    t = Trace()
    t.append(e1)
    t.append(e2)
    t.append(e3)
    t.append(e4)
    l.append(t)



    #
    # *---A---* 
    #           *--A--*
    #                   *--B--*    

    e1 = Event()
    e2 = Event()
    e3 = Event()

    e1[DEFAULT_NAME_KEY] = 'A'
    e1[DEFAULT_START_TIMESTAMP_KEY] = datetime.now()
    e1[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=1)

    e2[DEFAULT_NAME_KEY] = 'A'
    e2[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2)
    e2[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2.5)

    e3[DEFAULT_NAME_KEY] = 'B'
    e3[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=3)
    e3[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=3.5)

    t = Trace()
    t.append(e1)
    t.append(e2)
    t.append(e3)
    l.append(t)

    #
    # *---A---* 
    #           *--B--*    

    e1 = Event()
    e2 = Event()
    e1[DEFAULT_NAME_KEY] = 'A'
    e1[DEFAULT_START_TIMESTAMP_KEY] = datetime.now()
    e1[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=1)

    e2[DEFAULT_NAME_KEY] = 'B'
    e2[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2)
    e2[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2.5)

    t = Trace()
    t.append(e1)
    t.append(e2)
    l.append(t)

    #
    # *---A---* 
    #           *--B--*    
    #                    *--C--*

    e1 = Event()
    e2 = Event()
    e3 = Event()
    e1[DEFAULT_NAME_KEY] = 'A'
    e1[DEFAULT_START_TIMESTAMP_KEY] = datetime.now()
    e1[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=1)

    e2[DEFAULT_NAME_KEY] = 'B'
    e2[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2)
    e2[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2.5)

    e3[DEFAULT_NAME_KEY] = 'C'
    e3[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=3)
    e3[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=3.5)

    t = Trace()
    t.append(e1)
    t.append(e2)
    t.append(e3)
    l.append(t)

    #
    # *---H---* 
    #           *--B--*    
    #                    *--C--*

    e1 = Event()
    e2 = Event()
    e3 = Event()

    e1[DEFAULT_NAME_KEY] = 'H'
    e1[DEFAULT_START_TIMESTAMP_KEY] = datetime.now()
    e1[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=1)

    e2[DEFAULT_NAME_KEY] = 'B'
    e2[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2)
    e2[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2.5)

    e3[DEFAULT_NAME_KEY] = 'C'
    e3[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=3)
    e3[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=3.5)

    t = Trace()
    t.append(e1)
    t.append(e2)
    t.append(e3)
    l.append(t)

    #
    # *---H---* 
    #           *--B--*    
    #                    *--C--*

    e1 = Event()
    e2 = Event()
    e3 = Event()

    e1[DEFAULT_NAME_KEY] = 'H'
    e1[DEFAULT_START_TIMESTAMP_KEY] = datetime.now()
    e1[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=1)

    e2[DEFAULT_NAME_KEY] = 'B'
    e2[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2)
    e2[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2.5)

    e3[DEFAULT_NAME_KEY] = 'C'
    e3[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=3)
    e3[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=3.5)

    t = Trace()
    t.append(e1)
    t.append(e2)
    t.append(e3)
    l.append(t)

    #
    # *---A---* 
    #           *--B--*    
    #               *--C--*

    e1 = Event()
    e2 = Event()
    e3 = Event()

    e1[DEFAULT_NAME_KEY] = 'A'
    e1[DEFAULT_START_TIMESTAMP_KEY] = datetime.now()
    e1[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=1)

    e2[DEFAULT_NAME_KEY] = 'B'
    e2[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2)
    e2[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2.5)

    e3[DEFAULT_NAME_KEY] = 'C'
    e3[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2.25)
    e3[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=3)

    t = Trace()
    t.append(e1)
    t.append(e2)
    t.append(e3)
    l.append(t)

    #
    # *---A---* 
    #           *--B--*    
    #               *--C--*
    #             *--D--*

    e1 = Event()
    e2 = Event()
    e3 = Event()
    e4 = Event()

    e1[DEFAULT_NAME_KEY] = 'A'
    e1[DEFAULT_START_TIMESTAMP_KEY] = datetime.now()
    e1[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=1)

    e2[DEFAULT_NAME_KEY] = 'B'
    e2[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2)
    e2[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2.5)

    e3[DEFAULT_NAME_KEY] = 'C'
    e3[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2.25)
    e3[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=3)

    e4[DEFAULT_NAME_KEY] = 'D'
    e4[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2.1)
    e4[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2.75)


    t = Trace()
    t.append(e1)
    t.append(e2)
    t.append(e3)
    t.append(e4)
    l.append(t)

    #
    # *---A---* 
    #           *--B--*    
    #               *--C--*
    # *----------I-----------*


    e1 = Event()
    e2 = Event()
    e3 = Event()
    e4 = Event()

    e1[DEFAULT_NAME_KEY] = 'A'
    e1[DEFAULT_START_TIMESTAMP_KEY] = datetime.now()
    e1[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=1)

    e2[DEFAULT_NAME_KEY] = 'B'
    e2[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2)
    e2[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2.5)

    e3[DEFAULT_NAME_KEY] = 'C'
    e3[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2.25)
    e3[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=3)

    e4[DEFAULT_NAME_KEY] = 'I'
    e4[DEFAULT_START_TIMESTAMP_KEY] = datetime.now()
    e4[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=3.5)

    t = Trace()
    t.append(e1)
    t.append(e2)
    t.append(e3)
    t.append(e4)
    l.append(t)


    #
    # *---H---* 
    #           *--B--*    
    #                    *--C--*
    #           *-------G--------*

    e1 = Event()
    e2 = Event()
    e3 = Event()
    e4 = Event()

    e1[DEFAULT_NAME_KEY] = 'H'
    e1[DEFAULT_START_TIMESTAMP_KEY] = datetime.now()
    e1[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=1)

    e2[DEFAULT_NAME_KEY] = 'B'
    e2[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2)
    e2[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2.5)

    e3[DEFAULT_NAME_KEY] = 'C'
    e3[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=3)
    e3[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=3.5)

    e4[DEFAULT_NAME_KEY] = 'G'
    e4[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2)
    e4[DEFAULT_TIMESTAMP_KEY] = datetime.now() +timedelta(hours=3.75)

    t = Trace()
    t.append(e1)
    t.append(e2)
    t.append(e3)
    t.append(e4)
    l.append(t)

    #
    # *---H---* 
    #           *--B--*    
    #                    *--C--*
    #           *-------G--------*

    e1 = Event()
    e2 = Event()
    e3 = Event()
    e4 = Event()

    e1[DEFAULT_NAME_KEY] = 'H'
    e1[DEFAULT_START_TIMESTAMP_KEY] = datetime.now()
    e1[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=1)

    e2[DEFAULT_NAME_KEY] = 'B'
    e2[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2)
    e2[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2.5)

    e3[DEFAULT_NAME_KEY] = 'C'
    e3[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=3)
    e3[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=3.5)

    e4[DEFAULT_NAME_KEY] = 'G'
    e4[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2)
    e4[DEFAULT_TIMESTAMP_KEY] = datetime.now() +timedelta(hours=3.75)

    t = Trace()
    t.append(e1)
    t.append(e2)
    t.append(e3)
    t.append(e4)
    l.append(t)

    #
    # *---H---* 
    #           *--B--*    
    #                               *----K----*
    #                    *--C--*
    #           *-------G--------*

    e1 = Event()
    e2 = Event()
    e3 = Event()
    e4 = Event()
    e5 = Event()


    e1[DEFAULT_NAME_KEY] = 'H'
    e1[DEFAULT_START_TIMESTAMP_KEY] = datetime.now()
    e1[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=1)

    e2[DEFAULT_NAME_KEY] = 'B'
    e2[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2)
    e2[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2.5)

    e3[DEFAULT_NAME_KEY] = 'C'
    e3[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=3)
    e3[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=3.5)

    e4[DEFAULT_NAME_KEY] = 'G'
    e4[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2)
    e4[DEFAULT_TIMESTAMP_KEY] = datetime.now() +timedelta(hours=3.75)

    e5[DEFAULT_NAME_KEY] = 'K'
    e5[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=4.5)
    e5[DEFAULT_TIMESTAMP_KEY] = datetime.now() +timedelta(hours=6.75)

    t = Trace()
    t.append(e1)
    t.append(e2)
    t.append(e3)
    t.append(e4)
    t.append(e5)
    l.append(t)
    
    return l



def create_example_log_2(): 
    
    """
        →(H, ∧(G, →(B, C)), K)
        →(H, ∧(G, →(B, C))) ^2
        →(H, ∧(G, →(B, C)), ∧(O, P), K, L)^2
        →(H, ∧(G, →(B, C)), ∧(O, P), K)
        →(H, ∧(G, →(B, C)), ∧(O, P), K, M, N)
        →(A, B) ^2 
        →(H, B, C) ^ 2
        →(A, B, A, B)
        →(A, A, B)
        →(A, B, C)
        →(A, ∧(B, C))
        →(A, ∧(B, C, D))
        ∧(I, →(A, ∧(B, C)))
    """
    
    
    l = create_example_log_1()
    
    #
    # *---H---* 
    #           *--B--*    
    #                                    *--P--*  *----K----*
    #                    *--C--*     *--O--* 
    #           *-------G--------*

    e1 = Event()
    e2 = Event()
    e3 = Event()
    e4 = Event()
    e5 = Event()
    e6 = Event()
    e7 = Event()


    e1[DEFAULT_NAME_KEY] = 'H'
    e1[DEFAULT_START_TIMESTAMP_KEY] = datetime.now()
    e1[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=1)

    e2[DEFAULT_NAME_KEY] = 'B'
    e2[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2)
    e2[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2.5)

    e3[DEFAULT_NAME_KEY] = 'C'
    e3[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=3)
    e3[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=3.5)

    e4[DEFAULT_NAME_KEY] = 'G'
    e4[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2)
    e4[DEFAULT_TIMESTAMP_KEY] = datetime.now() +timedelta(hours=3.75)
    
    e5[DEFAULT_NAME_KEY] = 'O'
    e5[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=4)
    e5[DEFAULT_TIMESTAMP_KEY] = datetime.now() +timedelta(hours=5.25)
    
    e6[DEFAULT_NAME_KEY] = 'P'
    e6[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=5)
    e6[DEFAULT_TIMESTAMP_KEY] = datetime.now() +timedelta(hours=5.75)

    e7[DEFAULT_NAME_KEY] = 'K'
    e7[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=6)
    e7[DEFAULT_TIMESTAMP_KEY] = datetime.now() +timedelta(hours=6.75)

    t = Trace()
    t.append(e1)
    t.append(e2)
    t.append(e3)
    t.append(e4)
    t.append(e5)
    t.append(e6)
    t.append(e7)
    l.append(t)
    
    
    
    #
    # *---H---* 
    #           *--B--*    
    #                                    *--P--*   *----K----*
    #                    *--C--*     *--O--* 
    #           *-------G--------*

    e1 = Event()
    e2 = Event()
    e3 = Event()
    e4 = Event()
    e5 = Event()
    e6 = Event()
    e7 = Event()
    e8 = Event()


    e1[DEFAULT_NAME_KEY] = 'H'
    e1[DEFAULT_START_TIMESTAMP_KEY] = datetime.now()
    e1[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=1)

    e2[DEFAULT_NAME_KEY] = 'B'
    e2[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2)
    e2[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2.5)

    e3[DEFAULT_NAME_KEY] = 'C'
    e3[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=3)
    e3[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=3.5)

    e4[DEFAULT_NAME_KEY] = 'G'
    e4[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2)
    e4[DEFAULT_TIMESTAMP_KEY] = datetime.now() +timedelta(hours=3.75)
    
    e5[DEFAULT_NAME_KEY] = 'O'
    e5[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=4)
    e5[DEFAULT_TIMESTAMP_KEY] = datetime.now() +timedelta(hours=5.25)
    
    e6[DEFAULT_NAME_KEY] = 'P'
    e6[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=5)
    e6[DEFAULT_TIMESTAMP_KEY] = datetime.now() +timedelta(hours=5.75)

    e7[DEFAULT_NAME_KEY] = 'K'
    e7[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=6)
    e7[DEFAULT_TIMESTAMP_KEY] = datetime.now() +timedelta(hours=6.75)
    
    e8[DEFAULT_NAME_KEY] = 'L'
    e8[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=7)
    e8[DEFAULT_TIMESTAMP_KEY] = datetime.now() +timedelta(hours=8)

    t = Trace()
    t.append(e1)
    t.append(e2)
    t.append(e3)
    t.append(e4)
    t.append(e5)
    t.append(e6)
    t.append(e7)
    t.append(e8)
    l.append(t)
    
    
    #
    # *---H---* 
    #           *--B--*    
    #                                    *--P--*   *----K----* *--M--* *N*
    #                    *--C--*     *--O--* 
    #           *-------G--------*

    e1 = Event()
    e2 = Event()
    e3 = Event()
    e4 = Event()
    e5 = Event()
    e6 = Event()
    e7 = Event()
    e8 = Event()
    e9 = Event()
    e10 = Event()


    e1[DEFAULT_NAME_KEY] = 'H'
    e1[DEFAULT_START_TIMESTAMP_KEY] = datetime.now()
    e1[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=1)

    e2[DEFAULT_NAME_KEY] = 'B'
    e2[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2)
    e2[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2.5)

    e3[DEFAULT_NAME_KEY] = 'C'
    e3[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=3)
    e3[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=3.5)

    e4[DEFAULT_NAME_KEY] = 'G'
    e4[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2)
    e4[DEFAULT_TIMESTAMP_KEY] = datetime.now() +timedelta(hours=3.75)
    
    e5[DEFAULT_NAME_KEY] = 'O'
    e5[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=4)
    e5[DEFAULT_TIMESTAMP_KEY] = datetime.now() +timedelta(hours=5.25)
    
    e6[DEFAULT_NAME_KEY] = 'P'
    e6[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=5)
    e6[DEFAULT_TIMESTAMP_KEY] = datetime.now() +timedelta(hours=5.75)

    e7[DEFAULT_NAME_KEY] = 'K'
    e7[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=6)
    e7[DEFAULT_TIMESTAMP_KEY] = datetime.now() +timedelta(hours=6.75)
    
    e8[DEFAULT_NAME_KEY] = 'L'
    e8[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=7)
    e8[DEFAULT_TIMESTAMP_KEY] = datetime.now() +timedelta(hours=8)
    
    e9[DEFAULT_NAME_KEY] = 'M'
    e9[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=8.5)
    e9[DEFAULT_TIMESTAMP_KEY] = datetime.now() +timedelta(hours=9)
    
    e10[DEFAULT_NAME_KEY] = 'N'
    e10[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=9.5)
    e10[DEFAULT_TIMESTAMP_KEY] = datetime.now() +timedelta(hours=9.75)

    t = Trace()
    t.append(e1)
    t.append(e2)
    t.append(e3)
    t.append(e4)
    t.append(e5)
    t.append(e6)
    t.append(e7)
    t.append(e8)
    l.append(t)
    
    
    
    return l 




def create_example_log_3(): 
    
    """
        →(H, ∧(G, →(B, C)), K)
        →(H, ∧(G, →(B, C))) ^2
        →(H, ∧(G, →(B, C)), ∧(O, P), K, L)^2
        →(H, ∧(G, →(B, C)), ∧(O, P), K)
        →(H, ∧(G, →(B, C)), ∧(O, P), K, M, N)
        →(A, B) ^2 
        →(H, B, C) ^ 2
        →(A, B, A, B)
        →(A, A, B)
        →(A, B, C)
        →(A, ∧(B, C))
        →(A, ∧(B, C, D))
        ∧(I, →(A, ∧(B, C)))
        
        
    """
    
    
    l = create_example_log_2()
    
    
    
def create_example_log_fallthrough(): 
    


    e1 = Event()
    e2 = Event()
    e3 = Event()
    e4 = Event()
    
    
    #
    # *---A---*    *---C---*  
    #        *---B---*   *---D---* 
    #                               
    #                     

    l = EventLog()
    
    e1[DEFAULT_NAME_KEY] = 'A'
    e1[DEFAULT_START_TIMESTAMP_KEY] = datetime.now()
    e1[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=1)

    e2[DEFAULT_NAME_KEY] = 'B'
    e2[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=0.8)
    e2[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2)

    e3[DEFAULT_NAME_KEY] = 'C'
    e3[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours = 1.8)
    e3[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours= 3)

    e4[DEFAULT_NAME_KEY] = 'D'
    e4[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours= 2.8)
    e4[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=4)


    t = Trace()
    t.append(e1)
    t.append(e2)
    t.append(e3)
    t.append(e4)
    l.append(t)
    
    
    t = Trace()
    t.append(e1)
    t.append(e2)
    t.append(e3)
    t.append(e4)
    l.append(t)
    
    
    t = Trace()
    t.append(e1)
    t.append(e2)
    t.append(e3)
    t.append(e4)
    l.append(t)
    
    
    e1 = Event()
    e2 = Event()
    e3 = Event()
    e4 = Event()
    
    e1[DEFAULT_NAME_KEY] = 'B'
    e1[DEFAULT_START_TIMESTAMP_KEY] = datetime.now()
    e1[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=1)

    e2[DEFAULT_NAME_KEY] = 'C'
    e2[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=0.8)
    e2[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2)

    e3[DEFAULT_NAME_KEY] = 'D'
    e3[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours = 1.8)
    e3[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours= 3)

    e4[DEFAULT_NAME_KEY] = 'A'
    e4[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours= 2.8)
    e4[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=4)


    t = Trace()
    t.append(e1)
    t.append(e2)
    t.append(e3)
    t.append(e4)
    l.append(t)
    
    e1 = Event()
    e2 = Event()
    e3 = Event()
    e4 = Event()
    
    
    e1[DEFAULT_NAME_KEY] = 'B'
    e1[DEFAULT_START_TIMESTAMP_KEY] = datetime.now()
    e1[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=1)

    e2[DEFAULT_NAME_KEY] = 'A'
    e2[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=0.8)
    e2[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=2)

    e3[DEFAULT_NAME_KEY] = 'D'
    e3[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours = 1.8)
    e3[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours= 3)

    e4[DEFAULT_NAME_KEY] = 'C'
    e4[DEFAULT_START_TIMESTAMP_KEY] = datetime.now() + timedelta(hours= 2.8)
    e4[DEFAULT_TIMESTAMP_KEY] = datetime.now() + timedelta(hours=4)


    t = Trace()
    t.append(e1)
    t.append(e2)
    t.append(e3)
    t.append(e4)
    l.append(t)
    
    return l 
    
import pm4py