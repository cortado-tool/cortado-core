lexer grammar VQLLexer;
options {language=Python3;}

ISEVENTUALLYFOLLOWED : 'isEF' | 'isEventuallyFollowed'; 
ISDIRECTLYFOLLOWED : 'isDF' | 'isDirectlyFollowed';
ISCONCURRENT : 'isP' | 'isParallel'; 

ISSTARTTOKEN : 'isStart' | 'isS'; 
ISENDTOKEN : 'isEnd' | 'isE'; 
ISCONTAINED : 'isContained' | 'isC'; 

LPAR : '(';
RPAR : ')';

ANY : 'ANY'; 
ALL : 'ALL'; 

LCBRACKET : '{';
RCBRACKET : '}';

SEMICOLON : ';';
COMMA : ',';
GROUPINVERSE : '~';

EQUALS : '='; 
LT : '<'; 
GT : '>'; 


/* The logical concatenation operators*/
AND : 'AND';
OR : 'OR';
NOT : 'NOT';
IMPLIES : '->'; 

fragment LETTER : ('a'..'z'|'A'..'Z');

/* Natural Number Digits */
fragment NDIGIT :  ('1'..'9'); 

/*Digits + Zero*/
fragment DIGIT : '0' | NDIGIT;
fragment SPACE : ' '; 

fragment APOSTROPHE : '\''; 

/*Natural Numbers*/
NUMBER : NDIGIT (DIGIT)+ | DIGIT; 

SACTIVITY : APOSTROPHE -> more, mode(Activity);

// Skip Whitespace outside an Activity Name
WS : [ \n\t\r\f]+ -> skip;

mode Activity;

ACTIVITY :  APOSTROPHE -> mode(DEFAULT_MODE); 
ACTIVITYNAME : . -> more; 
