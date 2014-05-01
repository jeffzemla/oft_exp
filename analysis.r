library(data.table)
library(lmerTest)
library(ggplot2)
library(gridExtra)

path <- './logs/'

# import logs
log <- fread(sprintf('%s/biglog.csv',path))
setkey(log,subj)


# remove outliers, use only 1&5 min timed blocks
log[,select:= 0]
log[time==5,select := 1]
log[rt<.3 | rt>5,select := 0]
log[log[,sum(correct),by=list(subj,session)],sessionscore := V1] # not sure if this works, i think it needs multiple keys
log[log[,sum(correct),by=subj],totalscore:=V1]

log[log[select==1,mean(correct),by=subj],avgACC := V1] # avg accuracy per subj, but only for time 1&5 excluding RT outliers
log[avgACC < .6,select := 0] # excludes 5 participants < 60%

# set pre-cue and blocktype variables
log[,precue:=0]
log[,blocktype:=0]

log[cond==1 | cond==3 | cond==4,precue:=1]
log[cond==1 | cond== 2,blocktype := 3] # mixed
log[cond==3 | cond== 5,blocktype := 1] # easy
log[cond==4 | cond== 6,blocktype := 2] # hard

log[,session:=factor(session)]

rtres <- lmer(rt ~ precue*coh*session + (1|subj) + (1|precue:subj) + (1|coh:subj) + (1|session:subj),data=log[select==1])
summary(rtres)

accres <- lmer(correct ~ precue*coh*session + (1|subj) + (1|precue:subj) + (1|blocktype:subj),data=log[select==1])
summary(accres)

qplot(factor(coh),fill=factor(precue),y=rt,data=log[select==1],geom="bar",stat="summary",fun.y="mean",position="dodge")

# shorty <- log[select==1,list(rt=mean(rt),acc=mean(correct)),by=list(subj,precue,blocktype,coh,session)
# setkey(shorty,subj)
# accres <- aov(acc ~ precue*blocktype*coh*session + Error(subj),data=shorty)
# rtres <- aov(rt ~ precue*blocktype*coh*session + Error(subj),data=shorty)
# summary(accres)
# summary(rtres)
