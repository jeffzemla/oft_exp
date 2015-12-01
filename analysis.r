library(data.table)
library(lmerTest)
library(ggplot2)
#library(gridExtra)

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
    #log[log[,sum(correct),by=list(subj,session)],sessionscore := V1] # not sure if this works, i think it needs multiple keys
    log[log[,sum(correct),by=subj],totalscore:=V1]
    log[log[select==1,mean(correct),by=subj],avgACC := V1] # avg accuracy per subj, but only for time 5 excluding RT outliers
    log[avgACC < .6,select := 0] # excludes 5 participants < 60%
}

outliersPerSubj <- function () {
    log[,select:= 0]
    log[time==5,select := 1]

    ## !! i m p o r t a n t !!
    ## removes 3 subjects who had an incomplete session. is this what you want?
    log[subj==2 | subj==15 | subj==20,select:=0]
    
    outliers <- log[select==1,list(trials=tabulate(select)),by=subj]
    setkey(outliers,subj)
#    outliers[log[select==1 & rt > .18 & rt < 5,list(keep=tabulate(select)),by=subj],keep5:=keep]
    outliers[log[select==1 & rt > .18 & rt < 10,list(keep=tabulate(select)),by=subj],keep10:=keep]    
    outliers[log[,mean(avgACC),by=subj],avgACC := V1]
#    outliers[log[select==1,mean(correct),by=subj],avgACC := V1] 
#    outliers[log[select==1,mean(rt),by=subj],avgRT:=V1] 
#    outliers[,prop5:=keep5/trials]
    outliers[,prop10:=keep10/trials]
    outliers[,cutoff:=1]
#    outliers[avgACC<.6,cutoff:=1]
#    a <- qplot(subj,y=prop5,data=outliers,colour=cutoff) + scale_colour_gradient(low="black",high="red")
#    b <- qplot(subj,y=prop10,data=outliers,colour=cutoff) + scale_colour_gradient(low="black",high="red")
    #print(a)
    #dev.new()
    outliers[avgACC<.6,cutoff:=0] # reversed coding for colors... safe?    
    plotbasic <- theme_bw() + theme_classic(base_size=18) + theme(legend.key=element_blank(), plot.title=element_text(face="bold"))        
    b <- ggplot(data=outliers, aes(x=subj, y=prop10, color=factor(cutoff))) + geom_point(size=3) + plotbasic +
         ylab("Proportion of data kept") + xlab("Subject") +
         scale_color_discrete(name="Accuracy",breaks=c("0","1"),labels=c("< 60%","> 60%")) +
         theme(axis.ticks.x = element_blank(), axis.text.x = element_blank())    
    print(b)
    outliers
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
    log[precue==1 & blocktype==1,diffcond:=1] # coh 0.25
    log[precue==1 & blocktype==2,diffcond:=2] # coh 0.2
    log[precue==0 & blocktype==1,diffcond:=3]
    log[precue==0 & blocktype==2,diffcond:=4]
    log[precue==0 & blocktype==3 & coh==0.2, diffcond:=5]
    log[precue==0 & blocktype==3 & coh==0.25,diffcond:=6]
    log[precue==1 & blocktype==3 & coh==0.2, diffcond:=7]
    log[precue==1 & blocktype==3 & coh==0.25,diffcond:=8]
    log[session==2,diffcond:=diffcond+8]
    log[session==3,diffcond:=diffcond+16]    
    
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

log[blocktype==2,blocktype:=1] # reduce to two blocktypes, "mixed" and "solid"
log[,blocktype:=factor(blocktype)] # just in case

rtres <- lmer(rt ~ precue*coh*session*blocktype + (1|subj) + (1|precue:subj) + (1|coh:subj) + (1|session:subj) + (1|blocktype:subj),data=log[select==1])

accres <- lmer(correct ~ precue*coh*session*blocktype + (1|subj) + (1|precue:subj) + (1|coh:subj) + (1|session:subj) + (1|blocktype:subj),data=log[select==1])

### more selective analyses -- preferred 

## does varying difficulty affect RT/acc for a single coherence?
#rtreshard <- lmer(rt ~ precue*blocktype*session + (1|subj) + (1|precue:subj) + (1|blocktype:subj) + (1|session:subj),data=log[select==1 & coh==0.2])
#
#rtreseasy <- lmer(rt ~ precue*blocktype*session + (1|subj) + (1|precue:subj) + (1|blocktype:subj) + (1|session:subj),data=log[select==1 & coh==0.25])
#accreshard <- lmer(correct ~ precue*blocktype*session + (1|subj) + (1|precue:subj) + (1|blocktype:subj) + (1|session:subj),data=log[select==1 & coh==0.2])
#accreseasy <- lmer(correct ~ precue*blocktype*session + (1|subj) + (1|precue:subj) + (1|blocktype:subj) + (1|session:subj),data=log[select==1 & coh==0.25])
#
## does pre-cue have an effect on mixed blocks?
#
#rtresmixed <- lmer(rt ~ precue*coh*session + (1|subj) + (1|precue:subj) + (1|coh:subj) + (1|session:subj),data=log[select==1 & blocktype==3])
#accresmixed <- lmer(correct ~ precue*coh*session + (1|subj) + (1|precue:subj) + (1|coh:subj) + (1|session:subj),data=log[select==1 & blocktype==3])
#
##### blocktype and coh are dependent-- leave out blocktype and analyze separately. not interested in main effect anyway.
#
##rtres <- lmer(rt ~ precue*coh*session + (1|subj) + (1|precue:subj) + (1|coh:subj) + (1|session:subj),data=log[select==1])
##accres <- lmer(correct ~ precue*coh*session + (1|subj) + (1|precue:subj) + (1|coh:subj) + (1|session:subj),data=log[select==1])
##rtnosessres <- lmer(rt ~ precue*coh + (1|subj) + (1|precue:subj) + (1|coh:subj),data=log[select==1])
##accnosessres <- lmer(correct ~ precue*coh + (1|subj) + (1|precue:subj) + (1|coh:subj),data=log[select==1])
### acc & rt for mixed block
##rtmixedres <-  lmer(rt ~ precue*coh*session + (1|subj) + (1|precue:subj) + (1|coh:subj) + (1|session:subj),data=log[select==1 & blocktype==3])
##accmixedres <- lmer(correct ~ precue*coh*session + (1|subj) + (1|precue:subj) + (1|coh:subj) + (1|session:subj),data=log[select==1 & blocktype==3])
#   
## same no session var
##rtmixednosessres <-  lmer(rt ~ precue*coh + (1|subj) + (1|precue:subj) + (1|coh:subj),data=log[select==1 & blocktype==3])
##accmixednosessres <- lmer(correct ~ precue*coh + (1|subj) + (1|precue:subj) + (1|coh:subj),data=log[select==1 & blocktype==3])
#
#
##qplot(factor(coh),fill=factor(precue),y=rt,data=log[select==1],geom="bar",stat="summary",fun.y="mean",position="dodge")
#
## shorty <- log[select==1,list(rt=mean(rt),acc=mean(correct)),by=list(subj,precue,blocktype,coh,session)
## setkey(shorty,subj)
## accres <- aov(acc ~ precue*blocktype*coh*session + Error(subj),data=shorty)
## rtres <- aov(rt ~ precue*blocktype*coh*session + Error(subj),data=shorty)
## summary(accres)
## summary(rtres)
