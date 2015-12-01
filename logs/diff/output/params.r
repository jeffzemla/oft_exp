library(data.table)
library(ggplot2)
library(ez)
#library(gridExtra)
#library(Hmisc)
#library(lmerTest)

path <- '.'
numsubs <- 26 

# import logs

# should've learned about cast/melt in package(reshape) first...
mashTable <- function(qq,b=1) {
    
    if (b==1) {
        p1 <- qq[,list(s1b1p1d1),by=subj][,session:=1][,blocktype:=1][,precue:=1][,difficulty:=1]
        p2 <- qq[,list(s1b1p1d2),by=subj][,session:=1][,blocktype:=1][,precue:=1][,difficulty:=2]
        p3 <- qq[,list(s1b1p0d1),by=subj][,session:=1][,blocktype:=1][,precue:=0][,difficulty:=1]
        p4 <- qq[,list(s1b1p0d2),by=subj][,session:=1][,blocktype:=1][,precue:=0][,difficulty:=2]
        p9 <- qq[,list(s2b1p1d1),by=subj][,session:=2][,blocktype:=1][,precue:=1][,difficulty:=1]
        p10 <- qq[,list(s2b1p1d2),by=subj][,session:=2][,blocktype:=1][,precue:=1][,difficulty:=2]
        p11 <- qq[,list(s2b1p0d1),by=subj][,session:=2][,blocktype:=1][,precue:=0][,difficulty:=1]
        p12 <- qq[,list(s2b1p0d2),by=subj][,session:=2][,blocktype:=1][,precue:=0][,difficulty:=2]
        p17 <- qq[,list(s3b1p1d1),by=subj][,session:=3][,blocktype:=1][,precue:=1][,difficulty:=1]
        p18 <- qq[,list(s3b1p1d2),by=subj][,session:=3][,blocktype:=1][,precue:=1][,difficulty:=2]
        p19 <- qq[,list(s3b1p0d1),by=subj][,session:=3][,blocktype:=1][,precue:=0][,difficulty:=1]
        p20 <- qq[,list(s3b1p0d2),by=subj][,session:=3][,blocktype:=1][,precue:=0][,difficulty:=2]
    }
    p5 <- qq[,list(s1b3p1d1),by=subj][,session:=1][,blocktype:=3][,precue:=1][,difficulty:=1]
    p6 <- qq[,list(s1b3p1d2),by=subj][,session:=1][,blocktype:=3][,precue:=1][,difficulty:=2]
    p7 <- qq[,list(s1b3p0d1),by=subj][,session:=1][,blocktype:=3][,precue:=0][,difficulty:=1]
    p8 <- qq[,list(s1b3p0d2),by=subj][,session:=1][,blocktype:=3][,precue:=0][,difficulty:=2]
    p13 <- qq[,list(s2b3p1d1),by=subj][,session:=2][,blocktype:=3][,precue:=1][,difficulty:=1]
    p14 <- qq[,list(s2b3p1d2),by=subj][,session:=2][,blocktype:=3][,precue:=1][,difficulty:=2]
    p15 <- qq[,list(s2b3p0d1),by=subj][,session:=2][,blocktype:=3][,precue:=0][,difficulty:=1]
    p16 <- qq[,list(s2b3p0d2),by=subj][,session:=2][,blocktype:=3][,precue:=0][,difficulty:=2]
    p21 <- qq[,list(s3b3p1d1),by=subj][,session:=3][,blocktype:=3][,precue:=1][,difficulty:=1]
    p22 <- qq[,list(s3b3p1d2),by=subj][,session:=3][,blocktype:=3][,precue:=1][,difficulty:=2]
    p23 <- qq[,list(s3b3p0d1),by=subj][,session:=3][,blocktype:=3][,precue:=0][,difficulty:=1]
    p24 <- qq[,list(s3b3p0d2),by=subj][,session:=3][,blocktype:=3][,precue:=0][,difficulty:=2]
    
    if (b==1) {
        setnames(p1,"s1b1p1d1","param")
        setnames(p2,"s1b1p1d2","param")
        setnames(p3,"s1b1p0d1","param")
        setnames(p4,"s1b1p0d2","param")
        setnames(p9,"s2b1p1d1","param")
        setnames(p10,"s2b1p1d2","param")
        setnames(p11,"s2b1p0d1","param")
        setnames(p12,"s2b1p0d2","param")
        setnames(p17,"s3b1p1d1","param")
        setnames(p18,"s3b1p1d2","param")
        setnames(p19,"s3b1p0d1","param")
        setnames(p20,"s3b1p0d2","param")
    }
    setnames(p5,"s1b3p1d1","param")
    setnames(p6,"s1b3p1d2","param")
    setnames(p7,"s1b3p0d1","param")
    setnames(p8,"s1b3p0d2","param")
    setnames(p13,"s2b3p1d1","param")
    setnames(p14,"s2b3p1d2","param")
    setnames(p15,"s2b3p0d1","param")
    setnames(p16,"s2b3p0d2","param")
    setnames(p21,"s3b3p1d1","param")
    setnames(p22,"s3b3p1d2","param")
    setnames(p23,"s3b3p0d1","param")
    setnames(p24,"s3b3p0d2","param")
   
    if (b==1) {
        newtable <- rbind(p1,p2,p3,p4,p5,p6,p7,p8,p9,p10,p11,p12,p13,p14,p15,p16,p17,p18,p19,p20,p21,p22,p23,p24)
    } else {
        newtable <- rbind(p5,p6,p7,p8,p13,p14,p15,p16,p21,p22,p23,p24)
    }
    newtable
}

processLog <- function(logfile,b=1) {
    log <- fread(capture.output(cat(path,'/',logfile,sep="")))
    setkey(log,subj)
    log <- mashTable(log,b)
    
    # change everything to a factor
    log$subj <- factor(log$subj)
    log$precue <- factor(log$precue) 
    log$session <- factor(log$session)
    log$blocktype <- factor(log$blocktype)
    log$difficulty <- factor(log$difficulty)
    log
}

# anova for a,v,ter

a <- processLog('a.csv')
v <- processLog('v.csv')
ter <- processLog('ter.csv')
ao <- processLog('ao-multi.csv',0)

ares <- aov(param ~ precue*session*blocktype*difficulty + Error(subj/(precue*session*blocktype*difficulty)),data=a)
vres <- aov(param ~ precue*session*blocktype*difficulty + Error(subj/(precue*session*blocktype*difficulty)),data=v)
terres <- aov(param ~ precue*session*blocktype*difficulty + Error(subj/(precue*session*blocktype*difficulty)),data=ter)

plotbasic <- theme_bw() + theme_classic(base_size=18) + theme(legend.key=element_blank(), plot.title=element_text(face="bold"))    

d <- ggplot(data=v[,list(v=mean(param)),by=list(session,blocktype)],
      aes(x=factor(session), y=v, group=factor(blocktype), color=factor(blocktype), shape=factor(blocktype))) +
     geom_line(stat="identity",size=1) + geom_point(size=3) + plotbasic +
     scale_color_discrete(name="Block type",breaks=c("1","3"),labels=c("Static","Mixed")) +
     scale_shape_discrete(name="Block type",breaks=c("1","3"),labels=c("Static","Mixed")) + 
     scale_y_continuous(breaks=c(0,0.1,0.2,0.3)) +
     coord_cartesian(ylim=c(0.0,0.3)) +
     xlab("Session") +
     ylab("Drift rate")
 print(d)

dev.new()
e <- ggplot(data=ter[,list(ter=mean(param)),by=list(session,blocktype)],
      aes(x=factor(session), y=ter, group=factor(blocktype), color=factor(blocktype), shape=factor(blocktype))) +
     geom_line(stat="identity",size=1) + geom_point(size=3) + plotbasic +
     scale_color_discrete(name="Block type",breaks=c("1","3"),labels=c("Static","Mixed")) +
     scale_shape_discrete(name="Block type",breaks=c("1","3"),labels=c("Static","Mixed")) + 
     scale_y_continuous(breaks=c(0,0.1,0.2,0.3,0.4,0.5)) +
     coord_cartesian(ylim=c(0.0,0.5)) +
     xlab("Session") +
     ylab("Non-decision time")
 print(e)

f <- ggplot(data=v[,list(v=mean(param)),by=list(session,difficulty)],
      aes(x=factor(session), y=v, group=factor(difficulty), color=factor(difficulty), shape=factor(difficulty))) +
     geom_line(stat="identity",size=1) + geom_point(size=3) + plotbasic +
     scale_color_discrete(name="Difficulty",breaks=c("1","2"),labels=c("Easy","Hard")) +
     scale_shape_discrete(name="Difficulty",breaks=c("1","2"),labels=c("Easy","Hard")) + 
     scale_y_continuous(breaks=c(0,0.1,0.2,0.3)) +
     coord_cartesian(ylim=c(0.0,0.3)) +
     xlab("Session") +
     ylab("Drift rate")
 print(f)


#dev.new()
#d <- ggplot(data=a[blocktype==3,list(rt=mean(rt)),by=list(type,session)],
#      aes(x=factor(session), y=rt, group=factor(type), color=factor(type), shape=factor(type), linetype=factor(type))) +
#     geom_line(stat="identity",size=1) + geom_point(size=3,legend=FALSE) + plotbasic +
#     scale_linetype_manual(values=c("solid","dotted","solid","dotted"),
#                        name="type",labels=c("hard no PC","hard PC", "easy no PC","easy PC")) +
#     scale_color_manual(values=c("#F8766D","#F8766D","#00BFC4","#00BFC4"),
#                        name="type",labels=c("hard no PC","hard PC", "easy no PC","easy PC")) +
#     scale_shape_discrete(name="type",breaks=c("1","2","3","4"),labels=c("hard no PC","hard PC", "easy no PC","easy PC")) +
#     xlab("Session") +
#     ylab("Response time (in seconds)") +
#    # coord_cartesian(ylim=c(0.65,1.2)) + 
#     ggtitle("Mixed block")     
#
#h <- ggplot(data=log[select==1 & blocktype==1,list(rt=mean(rt)),by=list(type,session)],
#      aes(x=factor(session), y=rt, group=factor(type), color=factor(type), shape=factor(type), linetype=factor(type))) +
#     geom_line(stat="identity",size=1) + geom_point(size=3,legend=FALSE) + plotbasic +
#     scale_linetype_manual(values=c("solid","dotted","solid","dotted"),
#                        name="type",labels=c("hard no PC","hard PC", "easy no PC","easy PC")) +
#     scale_color_manual(values=c("#F8766D","#F8766D","#00BFC4","#00BFC4"),
#                        name="type",labels=c("hard no PC","hard PC", "easy no PC","easy PC")) +
#     scale_shape_discrete(name="type",breaks=c("1","2","3","4"),labels=c("hard no PC","hard PC", "easy no PC","easy PC")) +
#     xlab("Session") +
#     ylab("Response time (in seconds)") +
#   #  coord_cartesian(ylim=c(0.65,1.2)) + 
#     ggtitle("Static block")
#
#j <- grid.arrange(d,h,ncol=2)
#print(j)

 
