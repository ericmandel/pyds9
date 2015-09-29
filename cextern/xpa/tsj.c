/* gcc -g -Wall -o tsj tsj.c -I. -L. -lxpa */
#include <xpa.h>
#include <string.h>
#include <setjmp.h>

#define MAXB 1024
#define GB (1024 * 1024 * 1024)

char *xmalloc(int size);
void xfree(char *buf);

int main(int argc, char **argv)
{
  char iter=0;
  int i=0;
  int n=0;
  char tbuf[100];
  char *bufs[MAXB];
  jmp_buf env;

loop:
  iter++;
  if( setjmp(env) == 0 ){
    XPASaveJmp((void *)env);
    fprintf(stdout, "continue? ");
    fgets(tbuf, 99, stdin);
    if( *tbuf != 'y' ){
      fprintf(stdout, "exiting ...\n");
      return 0;
    }
    else{
      fprintf(stderr, "allocating ...\n");
      for(n=0; n<MAXB; n++){
	bufs[n] = (char *)xmalloc(GB);
	memset(bufs[n], iter, GB);
	fprintf(stderr, "%d\n", n);
      }
    }
  }
  else{
    for(i=0; i<n+1; i++){
      if( bufs[i] ) xfree(bufs[i]);
    }
    n = 0;
    fprintf(stderr, "freed up memory for next iteration\n");
    goto loop;
  }
  return 0;
}
