library(data.table)
library(ggplot2)
library(ez)
#library(gridExtra)
#library(Hmisc)
#library(lmerTest)

path <- '.'
numsubs <- 26 

# import logs

mashTable <- function(qq) {
    
    p1 <- qq[,list(b1p1d1),by=subj][,blocktype:=1][,precue:=1][,difficulty:=1]
    p2 <- qq[,list(b1p1d2),by=subj][,blocktype:=1][,precue:=1][,difficulty:=2]
    p3 <- qq[,list(b1p0d1),by=subj][,blocktype:=1][,precue:=0][,difficulty:=1]
    p4 <- qq[,list(b1p0d2),by=subj][,blocktype:=1][,precue:=0][,difficulty:=2]
    p5 <- qq[,list(b3p1d1),by=subj][,blocktype:=3][,precue:=1][,difficulty:=1]
    p6 <- qq[,list(b3p1d2),by=subj][,blocktype:=3][,precue:=1][,difficulty:=2]
    p7 <- qq[,list(b3p0d1),by=subj][,blocktype:=3][,precue:=0][,difficulty:=1]
    p8 <- qq[,list(b3p0d2),by=subj][,blocktype:=3][,precue:=0][,difficulty:=2]
    
    setnames(p1,"b1p1d1","param")
    setnames(p2,"b1p1d2","param")
    setnames(p3,"b1p0d1","param")
    setnames(p4,"b1p0d2","param")
    setnames(p5,"b3p1d1","param")
    setnames(p6,"b3p1d2","param")
    setnames(p7,"b3p0d1","param")
    setnames(p8,"b3p0d2","param")
   
    newtable <- rbind(p1,p2,p3,p4,p5,p6,p7,p8)
    newtable
}

processLog <- function(logfile) {
    log <- fread(capture.output(cat(path,'/',logfile,sep="")))
    setkey(log,subj)
    log <- mashTable(log)
    
    # change everything to a factor
    log$subj <- factor(log$subj)
    log$precue <- factor(log$precue) 
    log$blocktype <- factor(log$blocktype)
    log$difficulty <- factor(log$difficulty)
    log
}

# anova for a,v,ter

a <- processLog('a.csv')
v <- processLog('v.csv')
ter <- processLog('ter.csv')

ares <- aov(param ~ precue*blocktype*difficulty + Error(subj/(precue*blocktype*difficulty)),data=a)
vres <- aov(param ~ precue*blocktype*difficulty + Error(subj/(precue*blocktype*difficulty)),data=v)
terres <- aov(param ~ precue*blocktype*difficulty + Error(subj/(precue*blocktype*difficulty)),data=ter)
