﻿ÃƒÂ¯Ã‚Â¿Ã‚Â½ÃƒÂ¯Ã‚Â¿Ã‚Â½i m p o r t   p a n d a s   a s   p d 
 
 #   L o a d   t h e   C S V   f i l e 
 f i l e _ p a t h   =   " A A P L _ s t o c k _ d a t a . c s v "     #   U p d a t e   t h i s   w i t h   y o u r   a c t u a l   f i l e   n a m e 
 d f   =   p d . r e a d _ c s v ( f i l e _ p a t h ) 
 
 #   D i s p l a y   f i r s t   f e w   r o w s 
 p r i n t ( " \ n =ÃƒÂ¯Ã‚Â¿Ã‚Â½
ÃƒÂ¯Ã‚Â¿Ã‚Â½  I n i t i a l   D a t a   P r e v i e w : \ n " ,   d f . h e a d ( ) ) 
 
 #   C h e c k   t h e   c o l u m n   n a m e s 
 p r i n t ( " \ n =ÃƒÂ¯Ã‚Â¿Ã‚Â½ÃƒÂ¯Ã‚Â¿Ã‚Â½ÃƒÂ¯Ã‚Â¿Ã‚Â½  C o l u m n   N a m e s : " ,   d f . c o l u m n s ) 
 
 #   C h e c k   d a t a   t y p e s 
 p r i n t ( " \ n =ÃƒÂ¯Ã‚Â¿Ã‚Â½ÃƒÂ¯Ã‚Â¿Ã‚Â½ÃƒÂ¯Ã‚Â¿Ã‚Â½  C o l u m n   D a t a   T y p e s : \ n " ,   d f . d t y p e s ) 
 
 #   C h e c k   u n i q u e   v a l u e s   i n   e a c h   c o l u m n 
 f o r   c o l   i n   d f . c o l u m n s : 
         p r i n t ( f " \ n =ÃƒÂ¯Ã‚Â¿Ã‚Â½ÃƒÂ¯Ã‚Â¿Ã‚Â½  U n i q u e   V a l u e s   i n   { c o l } : \ n " ,   d f [ c o l ] . u n i q u e ( ) ) 
 
 #   S a v e   a   c l e a n e d   v e r s i o n   w i t h o u t   t h e   f i r s t   t w o   r o w s   i f   n e e d e d 
 d f _ c l e a n e d   =   d f . i l o c [ 2 : ] . r e s e t _ i n d e x ( d r o p = T r u e )     #   S k i p   f i r s t   t w o   r o w s 
 d f _ c l e a n e d . t o _ c s v ( " c l e a n e d _ d a t a . c s v " ,   i n d e x = F a l s e ) 
 p r i n t ( " \ n '  C l e a n e d   d a t a   s a v e d   a s   ' c l e a n e d _ d a t a . c s v ' " ) 
 
 

