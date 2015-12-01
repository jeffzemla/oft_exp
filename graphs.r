library(data.table)
library(lmerTest)
library(ggplot2)
library(gridExtra)

path <- './logs/'

# import logs
log <- fread(sprintf('%s/biglog.csv',path))
log[,subj:=factor(subj)]
setkey(log,subj)


# remove outliers, use only 5 min timed blocks
filterData <- function() {
    log[,select:= 0]
    log[time==5,select := 1]

    ## !! i m p o r t a n t !!
    ## removes 3 subjects who had an incomplete session. is this what you want?
    log[subj==2 | subj==15 | subj==20,select:=0]
    
    log[rt<.18 | rt>10,select := 0]
#    log[log[,sum(correct),by=list(subj,session)],sessionscore := V1] # not sure if this works, i think it needs multiple keys
    log[log[,sum(correct),by=subj],totalscore:=V1]
    log[log[select==1,mean(correct),by=subj],avgACC := V1] # avg accuracy per subj, but only for time 5 excluding RT outliers
    log[avgACC < .6,select := 0] # excludes 5 participants < 60%
}

filterData()

# set pre-cue and blocktype variables
log[,precue:=0]
log[,blocktype:=0]

log[cond==1 | cond==3 | cond==4,precue:=1]
log[cond==1 | cond== 2,blocktype := 3] # mixed
log[cond==3 | cond== 5,blocktype := 1] # easy
log[cond==4 | cond== 6,blocktype := 2] # hard

# convert everything to factor

log[,session:=factor(session)] 
log[,blocktype:=factor(blocktype)]
log[,precue:=factor(precue)]
log[,coh:=factor(coh)]

# collapsed across sessions
writeLogs <- function() {
    # set blocktypes for dmat analysis
    log[precue==1 & blocktype==1,diffcond:=1]
    log[precue==1 & blocktype==2,diffcond:=2]
    log[precue==0 & blocktype==1,diffcond:=3]
    log[precue==0 & blocktype==2,diffcond:=4]
    log[precue==0 & blocktype==3 & coh==0.2, diffcond:=5]
    log[precue==0 & blocktype==3 & coh==0.25,diffcond:=6]
    log[precue==1 & blocktype==3 & coh==0.2, diffcond:=7]
    log[precue==1 & blocktype==3 & coh==0.25,diffcond:=8]
    
    for (i in 1:32) {
        if(nrow(log[select == 1 & subj == i]) > 0) {
            if (i < 10) {
                filename <- capture.output(cat("./logs/diff/s00",i,".tab",sep=""))
            } else {
                filename <- capture.output(cat("./logs/diff/s0",i,".tab",sep=""))
            }
            write.table(log[select==1 & subj==i,list(diffcond,correct,rt)],sep="\t",file=filename,row.names=FALSE,col.names=FALSE)
        }
    }
}


log[blocktype==3 & coh==0.2 & precue==0, type:=1]
log[blocktype==3 & coh==0.2 & precue==1, type:=2]
log[blocktype==3 & coh==0.25 & precue==0, type:=3]
log[blocktype==3 & coh==0.25 & precue==1, type:=4]
log[blocktype==2 & precue==0, type:=5] # hard
log[blocktype==2 & precue==1, type:=6]
log[blocktype==1 & precue==0, type:=7] # easy
log[blocktype==1 & precue==1, type:=8] 

log[coh==0.2 & blocktype==2, type2:=1]
log[coh==0.2 & blocktype==3, type2:=2]
log[coh==0.25 & blocktype==1, type2:=3]
log[coh==0.25 & blocktype==3, type2:=4]

log[coh==0.2 & precue==0, type3:=1]
log[coh==0.2 & precue==1, type3:=2]
log[coh==0.25 & precue==0, type3:=3]
log[coh==0.25 & precue==1, type3:=4]


log[blocktype==2,blocktype:=1] # change blocktype to binary, static or mixed
log[,blocktype:=factor(blocktype)]

gg_color_hue <- function(n) {
  hues = seq(15, 375, length=n+1)
  hcl(h=hues, l=65, c=100)[1:n]
}

source('errorbars.r')

plotbasic <- theme_bw() + theme_classic(base_size=18) + theme(legend.key=element_blank(), plot.title=element_text(face="bold"))    

cdat<-summarySEwithin(data=log[select==1 & blocktype==3,list(acc=mean(correct)),by=list(subj,type,session)],idvar="subj",measurevar="acc",withinvars=c("type","session"))

c <- ggplot(cdat,
      aes(x=factor(session), y=acc, group=factor(type), color=factor(type), shape=factor(type), linetype=factor(type))) +
     geom_line(stat="identity",size=1) + geom_point(size=3,legend=FALSE) + plotbasic +
     scale_linetype_manual(values=c("solid","dotted","solid","dotted"),
                        name="type",labels=c("hard no PC","hard PC", "easy no PC","easy PC")) +
     scale_color_manual(values=c("#F8766D","#F8766D","#00BFC4","#00BFC4"),
                        name="type",   labels=c("hard no PC","hard PC", "easy no PC","easy PC")) +
     scale_shape_discrete(name="type",breaks=c("1","2","3","4"),labels=c("hard no PC","hard PC", "easy no PC","easy PC")) +
 #    geom_errorbar(width=.3, aes(ymin=acc-ci, ymax=acc+ci),position=position_dodge(),color="black") +
     xlab("Session") +
     ylab("Proportion correct") +
#     coord_cartesian(ylim=c(0.82,0.92)) +           
     coord_cartesian(ylim=c(0.75,1.0)) +                
     ggtitle("Mixed block")
      
dev.new()
gdat<-summarySEwithin(data=log[select==1 & blocktype==1,list(acc=mean(correct)),by=list(subj,type,session)],idvar="subj",measurevar="acc",withinvars=c("type","session"))

g <- ggplot(gdat,
      aes(x=factor(session), y=acc, group=factor(type), color=factor(type), shape=factor(type), linetype=factor(type))) +
     geom_line(stat="identity",size=1) + geom_point(size=3,legend=FALSE) + plotbasic +
     scale_linetype_manual(values=c("solid","dotted","solid","dotted"),
                        name="type",labels=c("hard no PC","hard PC", "easy no PC","easy PC")) +
     scale_color_manual(values=c("#F8766D","#F8766D","#00BFC4","#00BFC4"),
                        name="type",   labels=c("hard no PC","hard PC", "easy no PC","easy PC")) +
     scale_shape_discrete(name="type",breaks=c("1","2","3","4"),labels=c("hard no PC","hard PC", "easy no PC","easy PC")) +
     xlab("Session") +
     ylab("Proportion correct") +
#     coord_cartesian(ylim=c(0.82,0.92)) +      
     coord_cartesian(ylim=c(0.75,1.0)) +                
     ggtitle("Static block")

i <- grid.arrange(c,g,ncol=2)
print(i)     

dev.new()
ddat<-summarySEwithin(data=log[select==1 & blocktype==3,list(rt=mean(rt)),by=list(subj,type,session)],idvar="subj",measurevar="rt",withinvars=c("type","session"))

d <- ggplot(ddat,
      aes(x=factor(session), y=rt, group=factor(type), color=factor(type), shape=factor(type), linetype=factor(type))) +
     geom_line(stat="identity",size=1) + geom_point(size=3,legend=FALSE) + plotbasic +
     scale_linetype_manual(values=c("solid","dotted","solid","dotted"),
                        name="type",labels=c("hard no PC","hard PC", "easy no PC","easy PC")) +
     scale_color_manual(values=c("#F8766D","#F8766D","#00BFC4","#00BFC4"),
                        name="type",labels=c("hard no PC","hard PC", "easy no PC","easy PC")) +
     scale_shape_discrete(name="type",breaks=c("1","2","3","4"),labels=c("hard no PC","hard PC", "easy no PC","easy PC")) +
     xlab("Session") +
     ylab("Response time (in seconds)") +
     coord_cartesian(ylim=c(0.5,1.5)) +      
     ggtitle("Mixed block")     

hdat<-summarySEwithin(data=log[select==1 & blocktype==1,list(rt=mean(rt)),by=list(subj,type,session)],idvar="subj",measurevar="rt",withinvars=c("type","session"))

h <- ggplot(hdat,
      aes(x=factor(session), y=rt, group=factor(type), color=factor(type), shape=factor(type), linetype=factor(type))) +
     geom_line(stat="identity",size=1) + geom_point(size=3,legend=FALSE) + plotbasic +
     scale_linetype_manual(values=c("solid","dotted","solid","dotted"),
                        name="type",labels=c("hard no PC","hard PC", "easy no PC","easy PC")) +
     scale_color_manual(values=c("#F8766D","#F8766D","#00BFC4","#00BFC4"),
                        name="type",labels=c("hard no PC","hard PC", "easy no PC","easy PC")) +
     scale_shape_discrete(name="type",breaks=c("1","2","3","4"),labels=c("hard no PC","hard PC", "easy no PC","easy PC")) +
     xlab("Session") +
     ylab("Response time (in seconds)") +
     coord_cartesian(ylim=c(0.5,1.5)) +      
     ggtitle("Static block")

j <- grid.arrange(d,h,ncol=2)
print(j)


dev.new()
edat<-summarySEwithin(data=log[select==1,list(rt=mean(rt)),by=list(subj,type2,session)],idvar="subj",measurevar="rt",withinvars=c("type2","session"))

e <- ggplot(edat,
      aes(x=factor(session), y=rt, group=factor(type2), color=factor(type2), shape=factor(type2), linetype=factor(type2))) +
     geom_line(stat="identity",size=1) + geom_point(size=3,legend=FALSE) + plotbasic +
     scale_linetype_manual(values=c("solid","dotted","solid","dotted"),
                        name="type",labels=c("hard static","hard mixed", "easy static","easy mixed")) +
     scale_color_manual(values=c("#F8766D","#F8766D","#00BFC4","#00BFC4"),
                        name="type",labels=c("hard static","hard mixed", "easy static","easy mixed")) +
     scale_shape_discrete(name="type",breaks=c("1","2","3","4"),labels=c("hard static","hard mixed", "easy static","easy mixed")) +
     xlab("Session") +
     coord_cartesian(ylim=c(0.5,1.5)) +      
     ylab("Response time (in seconds)")

print(e)
 
dev.new()
fdat<-summarySEwithin(data=log[select==1,list(acc=mean(correct)),by=list(subj,type2,session)],idvar="subj",measurevar="acc",withinvars=c("type2","session"))

f <- ggplot(fdat,
      aes(x=factor(session), y=acc, group=factor(type2), color=factor(type2), shape=factor(type2), linetype=factor(type2))) +
     geom_line(stat="identity",size=1) + geom_point(size=3,legend=FALSE) + plotbasic +
     scale_linetype_manual(values=c("solid","dotted","solid","dotted"),
                        name="type",labels=c("hard static","hard mixed", "easy static","easy mixed")) +
     scale_color_manual(values=c("#F8766D","#F8766D","#00BFC4","#00BFC4"),
                        name="type",labels=c("hard static","hard mixed", "easy static","easy mixed")) +
     scale_shape_discrete(name="type",breaks=c("1","2","3","4"),labels=c("hard static","hard mixed", "easy static","easy mixed")) +
     coord_cartesian(ylim=c(0.75,1.0)) +                     
     xlab("Session") +
     ylab("Proportion correct")

print(f)

dev.new()
gdat<-summarySEwithin(data=log[select==1,list(rt=mean(rt)),by=list(subj,coh,session)],idvar="subj",measurevar="rt",withinvars=c("coh","session"))

g <- ggplot(gdat,
      aes(x=factor(session), y=rt, group=factor(coh), color=factor(coh), shape=factor(coh))) +
     geom_line(stat="identity",size=1) + geom_point(size=3,legend=FALSE) + plotbasic +
     xlab("Session") +
     ylab("Response time (seconds)") + 
     coord_cartesian(ylim=c(0.50,1.5)) +      
     scale_color_discrete(name="Difficulty",breaks=c("0.25","0.2"),labels=c("Easy","Hard")) +
     scale_shape_discrete(name="Difficulty",breaks=c("0.25","0.2"),labels=c("Easy","Hard"))
     

print(g)


dev.new()
e2dat<-summarySEwithin(data=log[select==1,list(rt=mean(rt)),by=list(subj,type3,session)],idvar="subj",measurevar="rt",withinvars=c("type3","session"))

e2 <- ggplot(e2dat,
      aes(x=factor(session), y=rt, group=factor(type3), color=factor(type3), shape=factor(type3), linetype=factor(type3))) +
     geom_line(stat="identity",size=1) + geom_point(size=3,show_guide=FALSE) + plotbasic +
     scale_linetype_manual(values=c("solid","dotted","solid","dotted"),
                        name="type",labels=c("hard no PC","hard PC", "easy no PC","easy PC")) +
     scale_color_manual(values=c("#F8766D","#F8766D","#00BFC4","#00BFC4"),
                        name="type",labels=c("hard no PC","hard PC", "easy no PC","easy PC")) +
     scale_shape_discrete(name="type",breaks=c("1","2","3","4"),labels=c("hard no PC","hard PC", "easy no PC","easy PC")) +
     xlab("Session") +
     coord_cartesian(ylim=c(0.5,1.5)) +      
     ylab("Response time (in seconds)")

print(e2)
 
dev.new()
f2dat<-summarySEwithin(data=log[select==1,list(acc=mean(correct)),by=list(subj,type3,session)],idvar="subj",measurevar="acc",withinvars=c("type3","session"))

f2 <- ggplot(f2dat,
      aes(x=factor(session), y=acc, group=factor(type3), color=factor(type3), shape=factor(type3), linetype=factor(type3))) +
     geom_line(stat="identity",size=1) + geom_point(size=3,show_guide=FALSE) + plotbasic +
     scale_linetype_manual(values=c("solid","dotted","solid","dotted"),
                        name="type",labels=c("hard no PC","hard PC", "easy no PC","easy PC")) +
     scale_color_manual(values=c("#F8766D","#F8766D","#00BFC4","#00BFC4"),
                        name="type",labels=c("hard no PC","hard PC", "easy no PC","easy PC")) +
     scale_shape_discrete(name="type",breaks=c("1","2","3","4"),labels=c("hard no PC","hard PC", "easy no PC","easy PC")) +
     coord_cartesian(ylim=c(0.75,1.0)) +                     
     xlab("Session") +
     ylab("Proportion correct")

print(f2)

